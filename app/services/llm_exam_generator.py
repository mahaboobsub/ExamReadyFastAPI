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
  "correctAnswer": "Correct option text or numerical answer",
  "explanation": "Detailed step-by-step solution",
  "bloomsLevel": "Remember|Understand|Apply|Analyze|Evaluate",
  "marks": 1|2|3|5|4,
  "difficulty": "Easy|Medium|Hard",
  "chapter": "Exact NCERT chapter name",
  "hasLatex": true|false,
  "keySteps": ["Step 1", "Step 2"]
}
"""
        
    async def generate_cbse_board_exam(
        self,
        board: str = "CBSE",
        class_num: int = 10,
        subject: str = "Mathematics",
        chapters: List[str] = None
    ) -> Dict:
        """
        Generate full CBSE board exam with proper chapter distribution
        """
        
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
                try:
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                         f.write(f"  Generating {qtype_config['count']} {qtype_config['type']}...\n")
                         
                    questions = await self._generate_questions_for_type(
                        chapter=chapter,
                        question_type=qtype_config['type'],
                        count=qtype_config['count'],
                        blooms_level=qtype_config['blooms'],
                        rag_context=rag_context
                    )
                    
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                         f.write(f"  ✅ Generated {len(questions)} questions.\n")
                    
                    all_questions.extend(questions)
                except Exception as e:
                    with open("board_gen_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"  ❌ Gen Error: {e}\n")
                    continue
        
        # STEP 3: Organize into sections
        exam = self._organize_into_sections(all_questions)
        
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
        Strategy: Distribute questions evenly across chapters
        """
        
        total_distribution = {
            'MCQ': {'count': 18, 'blooms': ['Remember', 'Understand', 'Apply']},
            'AR': {'count': 2, 'blooms': ['Understand', 'Apply']},
            'VSA': {'count': 5, 'blooms': ['Remember', 'Understand', 'Apply']},
            'SA': {'count': 6, 'blooms': ['Apply', 'Analyze']},
            'LA': {'count': 4, 'blooms': ['Apply', 'Analyze', 'Evaluate']},
            'CASE': {'count': 3, 'blooms': ['Apply', 'Analyze']}
        }
        
        num_chapters = len(chapters)
        distribution = []
        
        for i, chapter in enumerate(chapters):
            chapter_config = {
                'chapter': chapter,
                'question_types': []
            }
            
            # Distribute each question type
            for qtype, config in total_distribution.items():
                # Calculate questions for this chapter (round-robin)
                questions_for_chapter = config['count'] // num_chapters
                
                # Distribute remainder
                if i < (config['count'] % num_chapters):
                    questions_for_chapter += 1
                
                if questions_for_chapter > 0:
                    # Assign Bloom's level
                    blooms = config['blooms'][i % len(config['blooms'])]
                    
                    chapter_config['question_types'].append({
                        'type': qtype,
                        'count': questions_for_chapter,
                        'blooms': blooms
                    })
            
            if chapter_config['question_types']:
                distribution.append(chapter_config)
        
        return distribution
    
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
    
    async def _generate_questions_for_type(
        self,
        chapter: str,
        question_type: str,
        count: int,
        blooms_level: str,
        rag_context: str,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Generate questions for specific type with retry logic
        """
        
        # Helper to map bloom to difficulty
        def _map_blooms_to_difficulty(blooms: str) -> str:
            mapping = {
                "Remember": "Easy",
                "Understand": "Easy to Medium",
                "Apply": "Medium",
                "Analyze": "Medium to Hard",
                "Evaluate": "Hard"
            }
            return mapping.get(blooms, "Medium")

        # Helper for type requirements
        def _get_question_type_requirements(qtype: str) -> str:
            requirements = {
                "MCQ": "Format: 4 options (A-D), 1 correct. Plausible distractors.",
                "AR": "Format: Assertion-Reason. Use standard options (Both true, etc.)",
                "VSA": "Solvable in 2-3 mins. 1-2 steps. Direct application.",
                "SA": "Solvable in 4-5 mins. 3-4 steps. Show method.",
                "LA": "Solvable in 7-8 mins. 5-7 detailed steps. Multi-part allowed.",
                "CASE": "Scenario-based. 3-4 subquestions. Total 4 marks."
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
**Target Difficulty**: {_map_blooms_to_difficulty(blooms_level)}

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

5. **NCERT Alignment**:
   - Use the provided RAG context as your primary source.
   - If context is missing, use general NCERT knowledge for this topic.

### OUTPUT REQUIREMENTS
Generate EXACTLY {count} questions following the JSON schema.
Return as a JSON array: [{{ "text": "...", ... }}]
"""
        
        questions = []
        attempts = 0
        
        while len(questions) < count and attempts < max_retries:
            try:
                # Call Gemini
                response_text = await self.gemini.generate(
                    prompt=self.system_prompt + "\n" + prompt,
                    max_tokens=4000,
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
                print(f"Error generating questions ({chapter}/{question_type}): {e}")
                # FALLBACK: Generate Mock Questions if critical failure (e.g. Rate Limit)
                if attempts == max_retries - 1:
                    print(f"⚠️ Switching to MOCK generation for {chapter} {question_type}")
                    mock_qs = self._generate_mock_questions(chapter, question_type, count, blooms_level)
                    questions.extend(mock_qs)
                    break
                attempts += 1
                # Backoff
                await asyncio.sleep(1)
        
        return questions[:count]

    def _generate_mock_questions(self, chapter, qtype, count, blooms) -> List[Dict]:
        """Fallback generator when LLM fails"""
        mocks = []
        for i in range(count):
            q_data = {
                "text": f"[MOCK] Question {i+1} about {chapter} ({blooms}: {qtype}). Please ignore content quality.",
                "type": qtype,
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correctAnswer": "Option A",
                "explanation": "This is a placeholder explanation generated due to API Rate Limits.",
                "bloomsLevel": blooms,
                "difficulty": "Medium",
                "chapter": chapter,
                "marks": 1 if qtype=="MCQ" else 4 if qtype=="CASE" else 5 if qtype=="LA" else 3 if qtype=="SA" else 2
            }
            mocks.append(q_data)
        return mocks
    
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
