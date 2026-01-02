from typing import Dict, List
import uuid
import time
import json
import re
from app.config.cbse_templates import get_template
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.services.redis_service import redis_service
from app.services.deduplication import deduplicate_questions
from app.services.quality_scorer import calculate_quality_score, CUSTOM_QUALITY_THRESHOLD
from app.config.settings import settings

gemini = GeminiService()

class CustomExamGenerator:
    """
    Custom Exam Generator (Hybrid Mode)
    """
    
    def __init__(self):
        self.quality_threshold = CUSTOM_QUALITY_THRESHOLD
        self.qdrant_threshold = settings.QDRANT_FALLBACK_THRESHOLD
        self.over_fetch_ratio = 1.5
    
    async def generate(self, request: Dict) -> Dict:
        start_time = time.time()
        print(f"\n[CUSTOM] 🔧 Generating custom exam...")
        
        # 1. Cache Check
        cache_key = redis_service.generate_cache_key(request)
        cached = redis_service.get_cached_exam(cache_key)
        if cached:
            cached["latency_ms"] = int((time.time() - start_time) * 1000)
            cached["generation_method"] = "cached"
            return cached

        # 2. Setup
        template = get_template(request["template_id"])
        total_questions = sum(s["question_count"] for s in template.sections)
        chapters = request["chapters"]
        weightage = request["chapter_weightage"]
        
        # Calculate distribution per chapter
        chapter_dist = self._calculate_chapter_dist(chapters, weightage, total_questions)
        
        all_questions = []
        llm_used = False
        
        # 3. Fetch/Generate per Chapter
        for chapter, count in chapter_dist.items():
            if count == 0: continue
            
            # A. Try Qdrant
            qdrant_qs = await self._fetch_from_qdrant(
                template, chapter, count, request.get("difficulty", "Mixed")
            )
            
            print(f"[CUSTOM]   Chapter '{chapter}': Found {len(qdrant_qs)}/{count} in Qdrant")
            
            # B. Check Sufficiency
            if len(qdrant_qs) >= count:
                all_questions.extend(qdrant_qs[:count])
            else:
                # Add what we found
                all_questions.extend(qdrant_qs)
                missing = count - len(qdrant_qs)
                
                # C. LLM Fallback
                if missing > 0:
                    llm_used = True
                    print(f"[CUSTOM]   ⚠️ Fallback: Generating {missing} questions with Gemini...")
                    
                    context_chunks = await qdrant_service.search_ncert_context(
                        query=f"CBSE {template.class_num} {template.subject} {chapter}",
                        limit=5
                    )
                    
                    generated = await self._generate_with_gemini(
                        template, chapter, missing, request.get("difficulty"), context_chunks
                    )
                    all_questions.extend(generated)

        # 4. Deduplicate & Assign
        unique_qs = deduplicate_questions(all_questions)
        assigned_sections = self._assign_to_sections(unique_qs, template)
        
        # 5. Build Response
        response = {
            "exam_id": str(uuid.uuid4()),
            "mode": "custom",
            "template_id": request["template_id"],
            "sections": assigned_sections,
            "total_marks": template.total_marks,
            "chapters_covered": chapters,
            "generation_method": "real-time" if llm_used else "pre-generated",
            "latency_ms": int((time.time() - start_time) * 1000),
            "cache_key": cache_key
        }
        
        # 6. Cache Result
        redis_service.cache_exam(cache_key, response)
        
        return response

    def _calculate_chapter_dist(self, chapters, weightage, total):
        dist = {}
        assigned = 0
        for ch in chapters:
            w = weightage.get(ch, 0)
            n = int((w / 100) * total)
            dist[ch] = n
            assigned += n
        if assigned < total:
            dist[chapters[0]] += (total - assigned)
        return dist

    async def _fetch_from_qdrant(self, template, chapter, count, difficulty):
        # ✅ FIX: Use class_num
        filters = {
            "board": template.board,
            "class_num": template.class_num,
            "subject": template.subject,
            "chapter": chapter,
            "qualityScore": {"$gte": self.quality_threshold}
        }
        if difficulty != "Mixed":
            filters["difficulty"] = difficulty
            
        res = await qdrant_service.search_questions(
            query=f"{chapter} questions",
            filters=filters,
            limit=int(count * 1.5)
        )
        
        questions = []
        for chunk in res.get("chunks", []):
            meta = chunk.get("metadata", {})
            q = {
                "id": chunk["id"],
                "text": chunk["text"],
                "type": meta.get("question_type", "MCQ"),
                "marks": meta.get("marks", 1),
                "bloomsLevel": meta.get("bloomsLevel", "Understand"),
                "difficulty": meta.get("difficulty", difficulty),
                "chapter": chapter,
                "options": meta.get("options"),
                "correctAnswer": meta.get("correctAnswer"),
                "explanation": meta.get("explanation"),
                "sourceTag": meta.get("sourceTag", "QDRANT"),
                "qualityScore": meta.get("qualityScore", 0.0)
            }
            questions.append(q)
        return questions

    async def _generate_with_gemini(self, template, chapter, count, difficulty, context):
        context_text = "\n".join([c.get("text", "") for c in context])
        prompt = f"""
        Role: CBSE Exam Setter.
        Context: {context_text}
        Task: Create {count} questions for Class {template.class_num} {template.subject}, Chapter: {chapter}.
        Difficulty: {difficulty}.
        
        Mix of types: MCQ (1 mark), Short Answer (2-3 marks).
        
        OUTPUT JSON ARRAY:
        [{{
            "text": "Question?",
            "question_type": "MCQ", 
            "options": ["A","B","C","D"], 
            "correctAnswer": "A",
            "explanation": "...",
            "bloomsLevel": "Apply",
            "marks": 1
        }}]
        """
        
        try:
            txt = await gemini.generate(prompt, temperature=0.5, max_tokens=3000)
            from json_repair import repair_json
            data = json.loads(repair_json(txt))
            if isinstance(data, dict): data = [data]
            
            for q in data:
                q["id"] = str(uuid.uuid4())
                q["chapter"] = chapter
                q["difficulty"] = difficulty
                q["sourceTag"] = "GEMINI_FALLBACK"
                q["qualityScore"] = 0.75
                
            return data
        except Exception as e:
            print(f"[CUSTOM] ❌ LLM Error: {e}")
            return []

    def _assign_to_sections(self, questions, template):
        sections = {s['code']: [] for s in template.sections}
        
        for q in questions:
            # Use metadata type or default
            q_type = q.get("type", q.get("question_type", "MCQ"))
            assigned = False
            
            for s in template.sections:
                code = s['code']
                # ✅ FIX: Use correct template keys
                s_type = s['question_type']
                s_count = s['question_count']
                
                if s_type == q_type and len(sections[code]) < s_count:
                    q['section'] = code
                    sections[code].append(q)
                    assigned = True
                    break
            
            # ✅ FIX: Fallback assignment logic
            if not assigned:
                if q_type == "MCQ" and len(sections["A"]) < 20: sections["A"].append(q)
                elif q_type == "VSA" and len(sections["B"]) < 6: sections["B"].append(q)
                else: sections["C"].append(q) 
        
        return sections

custom_exam_generator = CustomExamGenerator()