from typing import Dict, List, Any
import uuid
import time
import asyncio
from fastapi import HTTPException
from app.config.cbse_templates import get_template
from app.services.qdrant_service import qdrant_service
from app.services.deduplication import deduplicate_questions
from app.services.quality_scorer import calculate_quality_score, BOARD_QUALITY_THRESHOLD
import logging

logger = logging.getLogger("examready")

class BoardExamGenerator:
    """
    Board Exam Generator (Strict Mode)
    ================================================
    Rules: 
    - Qdrant ONLY (no LLM generation)
    - No Caching
    - High Quality Threshold (0.85+)
    - Proper error propagation
    
    Changes in this version:
    - ✅ Removed manual subject mapping (Science -> [Physics, Chemistry, Biology])
    - ✅ Direct subject matching (template.subject matches database subject)
    - ✅ Robust section assignment with fallback
    - ✅ Error tracking with 30% failure threshold
    """
    
    def __init__(self):
        self.quality_threshold = BOARD_QUALITY_THRESHOLD
        self.over_fetch_ratio = 2.0  # Fetch 2x needed for deduplication buffer
    
    async def generate(self, template_id: str) -> Dict:
        start_time = time.time()
        
        # ========================================
        # 1. LOAD TEMPLATE
        # ========================================
        print(f"\n[BOARD] 📋 Generating board exam: {template_id}")
        template = get_template(template_id)
        
        total_questions = sum(s["question_count"] for s in template.sections)
        print(f"[BOARD] Target: {total_questions} questions across {len(template.sections)} sections")
        
        # ========================================
        # 2. BUILD PARALLEL QUERIES
        # ========================================
        tasks = []
        task_metadata = [] 
        
        # ✅ FIX: Use direct subject matching
        # No more ["Science", "Physics", "Chemistry", "Biology"] expansion
        # Database now has subject="Science" for all science questions
        target_subject = template.subject
        
        print(f"[BOARD] Querying for subject: '{target_subject}'")

        for section in template.sections:
            section_type = section["question_type"]  
            section_count = section["question_count"]
            
            # Distribute Bloom's taxonomy levels for this section
            blooms_dist = self._calculate_section_blooms(
                section, template.overall_blooms, section_count
            )
            
            # Create one query per Bloom's level
            for blooms_level, count in blooms_dist.items():
                if count == 0: 
                    continue
                
                # Fetch extra to account for deduplication
                fetch_limit = int(count * self.over_fetch_ratio)
                
                # Build filter criteria
                filters = {
                    "board": template.board,              # "CBSE"
                    "class_num": template.class_num,      # 10
                    "subject": target_subject,            # "Science" (direct match)
                    "question_type": section_type,        # "MCQ", "VSA", etc.
                    "bloomsLevel": blooms_level,          # "Remember", "Understand", etc.
                    "qualityScore": {"$gte": self.quality_threshold},  # 0.85+
                }
                
                # Semantic query text (helps with vector search)
                query_text = f"{template.board} {template.class_num} {target_subject} {section_type} {blooms_level} questions"
                
                # Create async task
                tasks.append(qdrant_service.search_questions(query_text, filters, fetch_limit))
                task_metadata.append(f"{blooms_level} ({section['code']})")

        # ========================================
        # 3. EXECUTE QUERIES IN PARALLEL
        # ========================================
        print(f"[BOARD] 🚀 Launching {len(tasks)} parallel Qdrant queries...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # ========================================
        # 4. ERROR TRACKING & FAIL-FAST
        # ========================================
        failed_count = 0
        all_candidates = []

        for i, res in enumerate(results):
            if isinstance(res, Exception):
                failed_count += 1
                logger.error(f"❌ Query failed for {task_metadata[i]}: {res}")
                continue
            
            chunks = res.get("chunks", [])
            if chunks:
                all_candidates.extend(chunks)
            else:
                logger.warning(f"⚠️ No results for {task_metadata[i]}")

        # ✅ CRITICAL: Fail fast if database is unstable
        if len(tasks) > 0:
            failure_rate = failed_count / len(tasks)
            if failure_rate > 0.30:  # 30% threshold
                raise HTTPException(
                    status_code=503,
                    detail=f"Database instability: {int(failure_rate*100)}% of queries failed. Please try again later."
                )

        print(f"[BOARD] 📦 Total candidates fetched: {len(all_candidates)} (Failures: {failed_count}/{len(tasks)})")
        
        # ========================================
        # 5. GLOBAL DEDUPLICATION
        # ========================================
        print(f"[BOARD] 🔍 Deduplicating candidates...")
        unique_questions = deduplicate_questions(all_candidates)
        
        if len(unique_questions) < total_questions:
            logger.warning(
                f"Insufficient unique questions: {len(unique_questions)}/{total_questions}. "
                f"Exam may be incomplete."
            )
            print(f"[BOARD] ⚠️ Warning: Only {len(unique_questions)}/{total_questions} unique questions available.")

        # ========================================
        # 6. PRIORITIZE BY SOURCE
        # ========================================
        # PYQ (Past Year Questions) > Sample Papers > NCERT Generated
        unique_questions.sort(key=lambda x: self._get_priority_score(x), reverse=True)
        
        # ========================================
        # 7. ASSIGN TO SECTIONS (TYPE-BASED)
        # ========================================
        assigned_sections = {}
        
        # Group questions by type for efficient allocation
        questions_by_type = {}
        for q in unique_questions:
            meta = q.get("metadata", {})
            # Normalize type field (handle both 'type' and 'question_type')
            q_type = meta.get("question_type") or meta.get("type") or "MCQ"
            
            if q_type not in questions_by_type:
                questions_by_type[q_type] = []
            questions_by_type[q_type].append(q)
        
        print(f"[BOARD] 📊 Question distribution by type:")
        for qtype, qlist in questions_by_type.items():
            print(f"   - {qtype}: {len(qlist)} questions")
        
        questions_flat_list = []
        
        for section in template.sections:
            code = section['code']
            count = section['question_count']
            target_type = section['question_type']
            marks = section['marks_per_question']
            
            section_qs = []
            
            # Get questions matching this section's type
            available = questions_by_type.get(target_type, [])
            
            # Take required count
            taken = available[:count]
            
            # Remove used questions from pool
            questions_by_type[target_type] = available[count:]
            
            # ✅ FALLBACK: If not enough of target type, use any available
            if len(taken) < count:
                needed = count - len(taken)
                print(f"[BOARD] ⚠️ Section {code} ({target_type}): Missing {needed} questions. Attempting fallback.")
                
                # Try other types in order of compatibility
                for fallback_type in questions_by_type:
                    if needed <= 0:
                        break
                    
                    fallback_pool = questions_by_type[fallback_type]
                    while fallback_pool and needed > 0:
                        taken.append(fallback_pool.pop(0))
                        needed -= 1
                
                if needed > 0:
                    logger.error(f"Section {code}: Still missing {needed} questions after fallback!")
            
            # Build section questions
            for q in taken:
                meta = q.get("metadata", {})
                flat_q = {
                    "id": q["id"],
                    "text": q["text"],
                    "type": target_type,  # Force to section type for consistency
                    "section": code,
                    "marks": marks,
                    "bloomsLevel": meta.get("bloomsLevel", "Understand"),
                    "difficulty": meta.get("difficulty", "Medium"),
                    "chapter": meta.get("chapter", "Unknown"),
                    "options": meta.get("options", []),
                    "correctAnswer": meta.get("correctAnswer", ""),
                    "explanation": meta.get("explanation", ""),
                    "sourceTag": meta.get("sourceTag", ""),
                    "qualityScore": meta.get("qualityScore", 0.0)
                }
                section_qs.append(flat_q)
                questions_flat_list.append(flat_q)
            
            assigned_sections[code] = section_qs
            print(f"[BOARD] Section {code}: Assigned {len(section_qs)}/{count} questions")

        # ========================================
        # 8. UPDATE USAGE COUNTS (ROTATION)
        # ========================================
        used_ids = [q['id'] for sec in assigned_sections.values() for q in sec]
        if used_ids:
            usage_tasks = [qdrant_service.increment_usage_count(qid) for qid in used_ids]
            await asyncio.gather(*usage_tasks, return_exceptions=True)
            print(f"[BOARD] 🔄 Updated usage counts for {len(used_ids)} questions")

        # ========================================
        # 9. FINAL RESPONSE
        # ========================================
        latency_ms = int((time.time() - start_time) * 1000)
        
        print(f"[BOARD] ✅ Exam generated in {latency_ms}ms")
        print(f"[BOARD] Final question count: {len(questions_flat_list)}/{total_questions}")
        
        return {
            "exam_id": str(uuid.uuid4()),
            "mode": "board",
            "template_id": template_id,
            "sections": assigned_sections,
            "questions": questions_flat_list,
            "total_marks": template.total_marks,
            "duration": template.duration_minutes,
            "chapters_covered": template.applicable_chapters,
            "generation_method": "pre-generated",
            "latency_ms": latency_ms
        }

    def _calculate_section_blooms(self, section: Dict, overall_blooms: Dict, count: int) -> Dict[str, int]:
        """
        Distributes questions across Bloom's taxonomy levels.
        
        Args:
            section: Section configuration
            overall_blooms: Template-level Bloom's distribution (percentages)
            count: Number of questions in this section
            
        Returns:
            Dictionary mapping Bloom's level to question count
        """
        dist = {}
        total_assigned = 0
        
        # Sort by percentage (descending) to handle largest chunks first
        sorted_blooms = sorted(overall_blooms.items(), key=lambda x: x[1], reverse=True)
        
        # Assign proportional counts to each level
        for level, pct in sorted_blooms[:-1]:
            num = round((pct / 100) * count)
            dist[level] = num
            total_assigned += num
        
        # Assign remainder to last level (ensures sum matches exactly)
        last_level = sorted_blooms[-1][0]
        dist[last_level] = max(0, count - total_assigned)
        
        return dist

    def _get_priority_score(self, question: Dict) -> int:
        """
        Calculates priority score for question selection.
        Higher score = higher priority.
        
        Scoring:
        - PYQ (Past Year Questions): +100
        - CBSE Sample Papers: +50
        - NCERT AI Generated: +10
        - Penalty: -5 per usage count (rotation)
        """
        meta = question.get("metadata", {})
        src = meta.get("sourceTag", "")
        usage = meta.get("usageCount", 0)
        
        score = 0
        
        # Source priority
        if "PYQ" in src:
            score += 100
        elif "CBSE_SAMPLE" in src:
            score += 50
        else:
            score += 10
        
        # Rotation penalty
        score -= (usage * 5)
        
        return score


# Singleton instance
board_exam_generator = BoardExamGenerator()
