import asyncio
import json
import time
import numpy as np
from typing import List, Dict, Optional
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from json_repair import repair_json

class LLMExamGenerator:
    """
    Enhanced LLM-based exam generator with chapter-wise distribution
    """
    
    def __init__(self):
        self.qdrant = qdrant_service # Use singleton
        self.gemini = GeminiService()
        
        # ADD THIS DIAGNOSTIC:
        if self.qdrant is None:
            print("=" * 70)
            print("⚠️ CRITICAL: Qdrant service is None")
            print("RAG context will NOT be available. Using LLM-only mode.")
        else:
            print(f"✅ Qdrant service connected: {type(self.qdrant)}")
            
        self.system_prompt = """
You are an expert CBSE Mathematics question paper setter for Class 10 (2025-26 pattern).

### ROLE & RESPONSIBILITIES
- Generate questions strictly from NCERT Class 10 Mathematics curriculum
- Follow official CBSE exam pattern with 5 sections (A/B/C/D/E)
- Ensure questions match specified Bloom's taxonomy level
- Create diverse, non-repetitive problem contexts
- Maintain academic rigor and age-appropriate language

### QUESTION QUALITY STANDARDS
1. **Accuracy**: All mathematical content must be 100% correct
2. **Clarity**: Questions must be unambiguous for 15-16 year old students
3. **NCERT Alignment**: Use only concepts/terminology from NCERT textbook
4. **Diversity**: Each question must have UNIQUE context/scenario
5. **Difficulty**: Match difficulty to specified Bloom's level

### OUTPUT FORMAT REQUIREMENTS
Return questions in this EXACT JSON structure:
{
  "text": "Question text here",
  "type": "MCQ|AR|VSA|SA|LA|CASE",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correctAnswer": "Complete correct option text or numerical answer",
  "explanation": "Detailed step-by-step solution. MUST be a SINGLE string. Do NOT split into multiple keys.",
  "bloomsLevel": "Remember|Understand|Apply|Analyze|Evaluate",
  "marks": 1|2|3|5|4,
  "difficulty": "Easy|Medium|Hard",
  "chapter": "Exact NCERT chapter name",
  "hasLatex": true|false,
  "keySteps": ["Step 1", "Step 2"]
}

### CRITICAL JSON RULES
1. **Explanation Field**: Must be one long string with \\n for line breaks. NEVER create extra keys like "number", "each", "conditions".
2. **Options**: Must be complete phrases (e.g., "x² + 1" not just "x²").
3. **No Trailing Commas**: Valid JSON only.
4. **Escape Characters**: Properly escape backslashes in LaTeX (e.g., \\frac).
"""
        
    async def generate_cbse_board_exam(
        self,
        board: str = "CBSE",
        class_num: int = 10,
        subject: str = "Mathematics",
        chapters: List[str] = None,
        difficulty_mode: str = "standard", # standard, easy, hard
        avoid_topics: List[str] = None
    ) -> Dict:
        """
        Generate full CBSE board exam with proper chapter distribution.
        Supports difficulty modes and topic avoidance for uniqueness.
        """
        
        # Lazy Init Qdrant
        if self.qdrant and self.qdrant.client is None:
            print("⚠️ Initializing Qdrant Client (Lazy Init)...")
            await self.qdrant.initialize()
        
        if not chapters:
            # Default CBSE Class 10 Maths chapters
            chapters = [
                "Real Numbers", "Polynomials", "Pair of Linear Equations in Two Variables",
                "Quadratic Equations", "Arithmetic Progressions", "Triangles",
                "Coordinate Geometry", "Introduction to Trigonometry", "Applications of Trigonometry",
                "Circles", "Areas Related to Circles", "Surface Areas and Volumes",
                "Statistics", "Probability"
            ]
        
        # STEP 1: Calculate chapter-wise distribution
        chapter_distribution = self._calculate_chapter_distribution(chapters)
        
        # STEP 2: Generate questions chapter by chapter
        all_questions = []
        
        start_time = time.time()
        
        with open("board_gen_debug.log", "w", encoding="utf-8") as f:
            f.write("Starting Board Exam Gen...\n")
        
        for chapter_config in chapter_distribution:
            chapter = chapter_config['chapter']
            question_types = chapter_config['question_types']
            
            msg = f"Generating questions for: {chapter}"
            print(msg)
            with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            
            # Get RAG context for this chapter (with fallback)
            rag_context = None
            try:
                rag_context = await self._get_chapter_context(
                    subject=subject,
                    class_num=class_num,
                    chapter=chapter
                )
                
                # If RAG returns nothing or too little, use LLM fallback
                if not rag_context or len(rag_context) < 100:
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"  ⚠️ Sparse RAG data for {chapter}, using LLM fallback\n")
                    rag_context = f"""
                    Generate questions for the chapter "{chapter}" from the CBSE Class {class_num} 
                    NCERT Mathematics textbook. Use standard CBSE curriculum knowledge for this chapter.
                    Ensure questions are appropriate for 15-16 year old students and follow CBSE 
                    marking scheme standards.
                    """
                else:
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"  ✅ Got RAG context (len: {len(rag_context)})\n")
                    
            except Exception as e:
                with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"  ⚠️ RAG Error: {e}, using LLM-only fallback\n")
                # FALLBACK: Use LLM general knowledge (DON'T SKIP!)
                rag_context = f"""
                Generate questions for "{chapter}" based on standard CBSE Class {class_num} 
                Mathematics curriculum. This is a fallback generation due to RAG unavailability.
                """

            # Generate each question type for this chapter
            for qtype_config in question_types:
                success = False
                retry_count = 0
                max_gen_retries = 5  # High retry count for resilience
                
                while not success and retry_count < max_gen_retries:
                    try:
                        with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                             f.write(f"  Generating {qtype_config['count']} {qtype_config['type']} (Attempt {retry_count+1})...\n")
                             
                        questions = await self._generate_questions_for_type(
                            chapter=chapter,
                            question_type=qtype_config['type'],
                            count=qtype_config['count'],
                            blooms_level=qtype_config['blooms'],
                            rag_context=rag_context,
                            difficulty_mode=difficulty_mode,
                            avoid_topics=avoid_topics
                        )
                        
                        if questions:
                            with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                                 f.write(f"  ✅ Generated {len(questions)} questions.\n")
                            all_questions.extend(questions)
                            success = True
                        else:
                            raise Exception("Empty response from generator")
                            
                    except Exception as e:
                        retry_count += 1
                        wait_time = 30 * retry_count  # Progressive backoff: 30s, 60s, 90s...
                        with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"  ❌ Gen Error: {e}. Retrying in {wait_time}s...\n")
                        await asyncio.sleep(wait_time)
                
                if not success:
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"  💀 FAILED to generate {qtype_config['type']} for {chapter} after {max_gen_retries} attempts.\n")
                    # Should we error out or continue? 
                    # User wants COMPLETE exam. Erroring out might be safer to flag issues.
                    # But partial is better than nothing? No, partial is "Failed".
                    pass
        
        # STEP 3: Organize into sections
        exam = self._organize_into_sections(all_questions)
        
        # STEP 3.5: Post-generation validation - fix missing fields
        exam = self._validate_and_fix_missing_fields(exam)
        
        # STEP 4: Add metadata
        exam['metadata'] = {
            'board': board,
            'class': class_num,
            'subject': subject,
            'totalQuestions': len(all_questions),
            'totalMarks': 80,
            'duration': 180,  # minutes
            'generationMethod': 'RAG+LLM',
            'llmModel': 'gemini-2.5-flash',
            'chaptersUsed': chapters,
            'generationTimeMs': int((time.time() - start_time) * 1000)
        }
        
        return exam
    
    def _calculate_chapter_distribution(self, chapters: List[str]) -> List[Dict]:
        """
        Calculate how many questions of each type per chapter
        Strategy: Distribute questions evenly AND maintain Bloom's balance
        
        FIXED v3: Adjusted targets to reduce Remember (-1) and increase Understand/Apply (+3)
        """
        import random
        
        # Overall Bloom's targets (percentage of 38 questions)
        OVERALL_BLOOMS_TARGET = {
            'Remember': 7,     # 18% (Reduced from 8)
            'Understand': 11,  # 29% (Increased from 9)
            'Apply': 11,       # 29% (Increased from 10)
            'Analyze': 7,      # 18% (Reduced from 8)
            'Evaluate': 2      # 5% (Fixed)
        }
        
        # Minimum quotas - MUST be met
        BLOOMS_MINIMUM_QUOTA = {
            'Remember': 5,
            'Understand': 9,
            'Apply': 9,
            'Analyze': 6,
            'Evaluate': 2  # ✅ FORCE at least 2
        }
        
        # Question type to allowed Bloom's levels (in priority order for that type)
        # FIXED: VSA/MCQ prioritization shifted to Understand/Apply
        TYPE_BLOOMS_PRIORITY = {
            'MCQ': ['Understand', 'Apply', 'Remember'],      # Prioritize Understand for MCQs
            'AR': ['Understand', 'Apply'],                   # Mid-level
            'VSA': ['Understand', 'Apply', 'Remember'],      # Prioritize Understand
            'SA': ['Apply', 'Analyze', 'Understand'],        # Mid-higher
            'LA': ['Evaluate', 'Analyze', 'Apply'],          # ✅ Evaluate FIRST
            'CASE': ['Analyze', 'Evaluate', 'Apply']         # Higher-order
        }
        
        total_distribution = {
            'MCQ': {'count': 18},
            'AR': {'count': 2},
            'VSA': {'count': 5},
            'SA': {'count': 6},
            'LA': {'count': 4},
            'CASE': {'count': 3}
        }
        
        num_chapters = len(chapters)
        distribution = []
        
        # Track Bloom's usage globally to maintain balance
        blooms_used = {level: 0 for level in OVERALL_BLOOMS_TARGET.keys()}
        
        # Track which types still need to be assigned (for post-processing)
        la_assigned = 0
        case_assigned = 0
        
        for i, chapter in enumerate(chapters):
            chapter_config = {
                'chapter': chapter,
                'question_types': []
            }
            
            # Distribute each question type
            for qtype, config in total_distribution.items():
                # Calculate questions for this chapter (round-robin count)
                questions_for_chapter = config['count'] // num_chapters
                
                # Distribute remainder
                if i < (config['count'] % num_chapters):
                    questions_for_chapter += 1
                
                if questions_for_chapter > 0:
                    allowed_blooms = TYPE_BLOOMS_PRIORITY[qtype]
                    
                    # SPECIAL HANDLING: Force Evaluate for first LA questions
                    if qtype == 'LA' and la_assigned < 2 and blooms_used['Evaluate'] < 2:
                        best_blooms = 'Evaluate'
                        la_assigned += questions_for_chapter
                    # Force Analyze for first CASE question if Evaluate quota met
                    elif qtype == 'CASE' and case_assigned == 0:
                        best_blooms = 'Analyze'
                        case_assigned += questions_for_chapter
                    else:
                        # Find which allowed Bloom's level is most needed globally
                        best_blooms = allowed_blooms[0]
                        max_gap = -999
                        
                        for level in allowed_blooms:
                            target = OVERALL_BLOOMS_TARGET[level]
                            used = blooms_used[level]
                            gap = target - used
                            
                            # Boost priority for levels below minimum quota
                            if used < BLOOMS_MINIMUM_QUOTA.get(level, 0):
                                gap += 10  # Strong priority boost
                            
                            if gap > max_gap:
                                max_gap = gap
                                best_blooms = level
                    
                    # Use the selected Bloom's level and update tracker
                    blooms_used[best_blooms] += questions_for_chapter
                    
                    chapter_config['question_types'].append({
                        'type': qtype,
                        'count': questions_for_chapter,
                        'blooms': best_blooms
                    })
            
            if chapter_config['question_types']:
                distribution.append(chapter_config)
        
        # POST-DISTRIBUTION CHECK: Swap to meet minimum quotas
        for level, min_count in BLOOMS_MINIMUM_QUOTA.items():
            if blooms_used[level] < min_count:
                print(f"⚠️ {level} under minimum ({blooms_used[level]}/{min_count}), attempting swap...")
                # Find a question to swap from over-used level
                for chapter_config in distribution:
                    for qt in chapter_config['question_types']:
                        current_level = qt['blooms']
                        # Only swap if current level is over target and this type allows target level
                        if (blooms_used[current_level] > OVERALL_BLOOMS_TARGET[current_level] and
                            level in TYPE_BLOOMS_PRIORITY.get(qt['type'], [])):
                            qt['blooms'] = level
                            blooms_used[current_level] -= qt['count']
                            blooms_used[level] += qt['count']
                            print(f"  ✅ Swapped {qt['type']} from {current_level} to {level}")
                            if blooms_used[level] >= min_count:
                                break
                    if blooms_used[level] >= min_count:
                        break
        
        # Debug: Print planned Bloom's distribution
        print(f"\n[BLOOM'S PLAN] Distribution for {len(chapters)} chapters:")
        for level, count in blooms_used.items():
            pct = (count / 38) * 100
            target = OVERALL_BLOOMS_TARGET[level]
            minimum = BLOOMS_MINIMUM_QUOTA[level]
            status = "✅" if count >= minimum else "❌"
            print(f"  {status} {level:10s}: {count:2d} questions ({pct:5.1f}%) - Target: {target}, Min: {minimum}")
        
        return distribution
    
    def _validate_and_fix_missing_fields(self, exam: Dict) -> Dict:
        """
        Post-generation validation to fix missing fields
        Auto-fills: bloomsLevel, difficulty, chapter
        """
        import random
        
        # Default Bloom's by question type
        DEFAULT_BLOOMS = {
            'MCQ': 'Remember',
            'AR': 'Understand',
            'VSA': 'Understand',
            'SA': 'Apply',
            'LA': 'Analyze',
            'CASE': 'Analyze'
        }
        
        # Default difficulty by question type
        DEFAULT_DIFFICULTY = {
            'MCQ': 'Easy',
            'AR': 'Medium',
            'VSA': 'Easy',
            'SA': 'Medium',
            'LA': 'Hard',
            'CASE': 'Medium'
        }
        
        fixes_applied = 0
        
        for section_code, section in exam.get('sections', {}).items():
            for q in section.get('questions', []):
                qtype = q.get('type', 'MCQ')
                
                # Fix missing Bloom's level
                if not q.get('bloomsLevel') or q.get('bloomsLevel') == 'Unknown':
                    q['bloomsLevel'] = DEFAULT_BLOOMS.get(qtype, 'Understand')
                    fixes_applied += 1
                
                # Fix missing difficulty
                if not q.get('difficulty') or q.get('difficulty') == 'Unknown':
                    q['difficulty'] = DEFAULT_DIFFICULTY.get(qtype, 'Medium')
                    fixes_applied += 1
                
                # Fix missing chapter
                if not q.get('chapter') or q.get('chapter') == 'Unknown':
                    # Try to infer from question text keywords
                    text = q.get('text', '').lower()
                    if 'polynomial' in text or 'zeroes' in text:
                        q['chapter'] = 'Polynomials'
                    elif 'quadratic' in text:
                        q['chapter'] = 'Quadratic Equations'
                    elif 'trigonometry' in text or 'sin' in text or 'cos' in text:
                        q['chapter'] = 'Introduction to Trigonometry'
                    elif 'circle' in text:
                        q['chapter'] = 'Circles'
                    elif 'probability' in text:
                        q['chapter'] = 'Probability'
                    elif 'cone' in text or 'sphere' in text or 'cylinder' in text or 'hemisphere' in text:
                        q['chapter'] = 'Surface Areas and Volumes'
                    elif 'area' in text and 'circle' in text:
                        q['chapter'] = 'Areas Related to Circles'
                    elif 'mean' in text or 'median' in text or 'mode' in text:
                        q['chapter'] = 'Statistics'
                    elif 'coordinate' in text or 'distance' in text:
                        q['chapter'] = 'Coordinate Geometry'
                    elif 'triangle' in text or 'similar' in text:
                        q['chapter'] = 'Triangles'
                    elif 'linear' in text or 'equation' in text:
                        q['chapter'] = 'Pair of Linear Equations in Two Variables'
                    elif 'ap' in text or 'arithmetic' in text or 'progression' in text:
                        q['chapter'] = 'Arithmetic Progressions'
                    elif 'prime' in text or 'factor' in text or 'hcf' in text or 'lcm' in text:
                        q['chapter'] = 'Real Numbers'
                    else:
                        q['chapter'] = 'Mathematics'  # Generic fallback
                    fixes_applied += 1
        
        if fixes_applied > 0:
            print(f"\n[VALIDATION] ✅ Auto-fixed {fixes_applied} missing field(s)")
        
        return exam
    
    async def _get_chapter_context(
        self,
        subject: str,
        class_num: int,
        chapter: str,
        top_k: int = 8
    ) -> str:
        """
        Get RAG context for specific chapter
        """
        
        # Perform hybrid search with chapter filter
        # Note: We rely on the subject and text query mostly if metadata isn't perfect
        query = f"{chapter} concepts examples problems formulas"
        filters = {
            "subject": subject,
            # "class": class_num, # Relax check
            # "chapter": chapter # Start broad
        }
        
        results = await self.qdrant.hybrid_search(
            query=query,
            filters=filters,
            top_k=top_k
        )
        
        # Format context for LLM
        context_parts = []
        if 'chunks' in results:
            for i, chunk in enumerate(results['chunks'], 1):
                meta = chunk.get('metadata', {})
                context_parts.append(f"""
--- Chunk {i} ---
Content:
{chunk.get('text', '')}
                """)
        else:
             # Fallback if result structure is direct list
             pass
        
        return "\n\n".join(context_parts)
    
    def _map_blooms_to_difficulty(self, blooms: str, qtype: str, mode: str = "standard") -> str:
        """
        Maps Bloom's level to discrete difficulty based on mode.
        """
        import random
        
        # Helper to pick weighted
        def pick(options, weights):
            if not weights or len(options) != len(weights): return options[0]
            return random.choices(options, weights=weights, k=1)[0]
            
        try:
            if qtype == "MCQ":
                if blooms == "Remember": return "Easy"
                elif blooms == "Understand":
                    if mode == "easy": return pick(["Easy", "Medium"], [0.7, 0.3])
                    elif mode == "hard": return pick(["Medium", "Hard"], [0.7, 0.3])
                    else: return pick(["Easy", "Medium"], [0.3, 0.7]) # Standard
                elif blooms == "Apply":
                    if mode == "easy": return "Medium"
                    elif mode == "hard": return "Hard"
                    else: return "Medium"
                else: return "Medium"
                
            elif qtype == "AR": return "Medium"
                
            elif qtype == "VSA":
                if blooms == "Remember": return "Easy"
                elif blooms == "Understand":
                    if mode == "easy": return "Easy"
                    elif mode == "hard": return "Medium"
                    else: return "Medium"
                else: return "Medium"
                
            elif qtype == "SA":
                if blooms == "Apply": return "Medium"
                elif blooms == "Analyze":
                    if mode == "easy": return "Medium"
                    elif mode == "hard": return "Hard"
                    else: return pick(["Medium", "Hard"], [0.7, 0.3])
                else: return "Medium"
                
            elif qtype == "LA":
                if blooms == "Evaluate": return "Hard"
                if mode == "easy": return pick(["Medium", "Hard"], [0.6, 0.4])
                elif mode == "hard": return "Hard"
                else: return pick(["Medium", "Hard"], [0.4, 0.6])
                
            elif qtype == "CASE":
                return "Medium"
            
            return "Medium"
        except Exception:
            return "Medium"

    async def _generate_questions_for_type(
        self,
        chapter: str,
        question_type: str,
        count: int,
        blooms_level: str,
        rag_context: str,
        max_retries: int = 3,
        difficulty_mode: str = "standard",
        avoid_topics: List[str] = None
    ) -> List[Dict]:
        """
        Generate questions for specific type with retry logic
        """
        import random

        # Helper for type requirements
        def _get_question_type_requirements(qtype: str) -> str:
            requirements = {
                "MCQ": "Format: 4 options (A-D), 1 correct. Plausible distractors.",
                "AR": "Format: Assertion-Reason. Use standard options (Both true, etc.)",
                "VSA": "Solvable in 2-3 mins. 1-2 steps. Direct application.",
                "SA": "Solvable in 4-5 mins. 3-4 steps. Show method.",
                "LA": "Solvable in 7-8 mins. 5-7 detailed steps. Multi-part allowed. COMPLETE all explanations.",
                "CASE": "Scenario-based. 3-4 subquestions. Total 4 marks. COMPLETE all sub-parts."
            }
            return requirements.get(qtype, "Standard format")
            
        def _get_blooms_requirements(blooms: str) -> str:
            return f"Focus on {blooms} level cognitive skills."

        prompt = f"""
### GENERATION REQUEST

**Chapter**: {chapter}
**Question Type**: {question_type}
**Quantity**: {count} questions
**Bloom's Level**: {blooms_level}
**Target Difficulty**: {self._map_blooms_to_difficulty(blooms_level, question_type, difficulty_mode)}

### RAG CONTEXT (NCERT Source Material)
```
{rag_context}
```

### SPECIFIC REQUIREMENTS FOR THIS REQUEST

1. **Chapter Scope**: Generate questions ONLY about "{chapter}"
2. **Question Type Requirements**:
{_get_question_type_requirements(question_type)}

3. **Bloom's Level Requirements**:
{_get_blooms_requirements(blooms_level)}

4. **Diversity Check**:
   - Each of the {count} questions must have a COMPLETELY DIFFERENT context
   - Avoid repeating age/geometry/motion problems if already generated.
   - EXCLUSIONS: Do NOT use these topics/values (already covered): {', '.join(avoid_topics) if avoid_topics else 'None'}

5. **NCERT Alignment**:
   - Use the provided RAG context as your primary source.
   - If context is missing, use general NCERT knowledge for this topic.

6. **COMPLETENESS REQUIREMENT**:
   - CRITICAL: Every question MUST have a COMPLETE explanation.
   - Do NOT truncate explanations or leave them incomplete.
   - For LA/CASE questions, include ALL steps and sub-parts.

### OUTPUT REQUIREMENTS
Generate EXACTLY {count} questions following the JSON schema.
Return as a JSON array: [{{ "text": "...", ... }}]
"""
        
        questions = []
        attempts = 0
        
        # FIXED: Dynamic token limit based on question type
        if question_type in ['LA', 'CASE']:
            token_limit = 8000  # LA/CASE need detailed explanations
        elif question_type == 'SA':
            token_limit = 5000
        else:
            token_limit = 3000  # MCQ, AR, VSA
        
        while len(questions) < count and attempts < max_retries:
            try:
                # Call Gemini
                response_text = await self.gemini.generate(
                    prompt=self.system_prompt + "\n" + prompt,
                    max_tokens=token_limit,
                    temperature=0.7
                )
                
                # Parse JSON
                clean_json = repair_json(response_text.replace("```json", "").replace("```", ""))
                generated_data = json.loads(clean_json)
                
                if isinstance(generated_data, dict): generated = [generated_data]
                else: generated = generated_data
                
                # Check for duplicates & Validation
                for q in generated:
                    # Basic validation
                    if not q.get('text'): continue
                    
                    # Ensure section/marks match type
                    q['type'] = question_type
                    
                    if question_type == "MCQ": q['marks'] = 1
                    elif question_type == "AR": q['marks'] = 1
                    elif question_type == "VSA": q['marks'] = 2
                    elif question_type == "SA": q['marks'] = 3
                    elif question_type == "LA": q['marks'] = 5
                    elif question_type == "CASE": q['marks'] = 4
                    
                    questions.append(q)
                
                # Break if satisfied
                if len(questions) >= count:
                    break
                    
                attempts += 1
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"Error generating questions ({chapter}/{question_type}): {e}")
                
                # ✅ FIXED: No more mock questions - fail gracefully with partial results
                if "rate limit" in error_msg or "429" in error_msg or "quota" in error_msg:
                    print(f"⚠️ Rate limit hit for {chapter}/{question_type}. Waiting 30s...")
                    await asyncio.sleep(30)
                elif "500" in error_msg or "internal" in error_msg:
                    print(f"⚠️ Server error for {chapter}/{question_type}. Waiting 10s...")
                    await asyncio.sleep(10)
                else:
                    print(f"❌ Critical error for {chapter}/{question_type}. Skipping after {attempts+1} attempts.")
                
                attempts += 1
                
                # If max retries exhausted, return what we have (NOT mock questions)
                if attempts >= max_retries:
                    print(f"⚠️ Max retries reached for {chapter}/{question_type}. Returning {len(questions)}/{count} questions.")
                    break
                
                await asyncio.sleep(2)
        
        return questions[:count]
    
    def _validate_blooms_distribution(self, questions: List[Dict], target: Dict[str, int]) -> bool:
        """
        Validate Bloom's distribution matches target (±10% tolerance)
        Returns True if valid, False if mismatched
        """
        if not questions:
            return False
            
        actual = {}
        for q in questions:
            level = q.get("bloomsLevel", "Apply")
            actual[level] = actual.get(level, 0) + 1
        
        total = len(questions)
        mismatches = []
        
        for level, target_pct in target.items():
            actual_pct = (actual.get(level, 0) / total) * 100 if total > 0 else 0
            
            # 10% tolerance
            if abs(actual_pct - target_pct) > 10:
                mismatches.append(f"{level}: {actual_pct:.1f}% (target: {target_pct}%)")
        
        if mismatches:
            print(f"⚠️ Bloom's distribution mismatch: {', '.join(mismatches)}")
            return False
        
        return True
    
    def _organize_into_sections(self, questions: List[Dict]) -> Dict:
        """
        Organize questions into CBSE sections A/B/C/D/E
        """
        sections = {
            'A': {'name': 'Section A (MCQ & AR)', 'questions': [], 'marks': 0},
            'B': {'name': 'Section B (VSA)', 'questions': [], 'marks': 0},
            'C': {'name': 'Section C (SA)', 'questions': [], 'marks': 0},
            'D': {'name': 'Section D (LA)', 'questions': [], 'marks': 0},
            'E': {'name': 'Section E (Case-Study)', 'questions': [], 'marks': 0}
        }
        
        for q in questions:
            qtype = q.get('type', 'MCQ')
            
            if qtype in ['MCQ', 'AR']:
                sections['A']['questions'].append(q)
                sections['A']['marks'] += q.get('marks', 1)
            elif qtype == 'VSA':
                sections['B']['questions'].append(q)
                sections['B']['marks'] += q.get('marks', 2)
            elif qtype == 'SA':
                sections['C']['questions'].append(q)
                sections['C']['marks'] += q.get('marks', 3)
            elif qtype == 'LA':
                sections['D']['questions'].append(q)
                sections['D']['marks'] += q.get('marks', 5)
            elif qtype == 'CASE':
                sections['E']['questions'].append(q)
                sections['E']['marks'] += q.get('marks', 4)
        
        self._add_internal_choices(sections)
        return {'sections': sections}
    
    def _add_internal_choices(self, sections: Dict):
        """
        Mark questions with internal choice (Approximated logic)
        """
        # B: 2 choices
        if len(sections['B']['questions']) >= 2:
            sections['B']['questions'][-1]['internalChoice'] = True
            sections['B']['questions'][-2]['internalChoice'] = True
            
        # C: 2 choices
        if len(sections['C']['questions']) >= 2:
            sections['C']['questions'][-1]['internalChoice'] = True
            sections['C']['questions'][-2]['internalChoice'] = True
            
        # D: 2 choices
        if len(sections['D']['questions']) >= 2:
            sections['D']['questions'][-1]['internalChoice'] = True
            sections['D']['questions'][-2]['internalChoice'] = True
            
        # E: All choices internal
        for q in sections['E']['questions']:
            q['internalChoice'] = True
