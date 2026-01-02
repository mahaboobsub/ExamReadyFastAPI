import sys
import os
import asyncio
import json
import uuid
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.settings import settings
from qdrant_client import models
from json_repair import repair_json 

# ========================================
# 🎯 CONFIGURATION: CBSE 2025-26 TARGETS
# Format: (Board Subject, Chapter Name, Textbook Subject)
# ========================================
TARGETS = [
    # --- MATHEMATICS (Class 10) ---
    # Ensure you have downloaded and indexed these PDFs first!
    ("Mathematics", "Real Numbers", "Maths"),
    ("Mathematics", "Polynomials", "Maths"),
    ("Mathematics", "Pair of Linear Equations in Two Variables", "Maths"),
    ("Mathematics", "Quadratic Equations", "Maths"),
    ("Mathematics", "Arithmetic Progressions", "Maths"),
    ("Mathematics", "Triangles", "Maths"),
    ("Mathematics", "Coordinate Geometry", "Maths"),
    ("Mathematics", "Introduction to Trigonometry", "Maths"),
    ("Mathematics", "Some Applications of Trigonometry", "Maths"),
    ("Mathematics", "Circles", "Maths"),
    ("Mathematics", "Areas Related to Circles", "Maths"),
    ("Mathematics", "Surface Areas and Volumes", "Maths"),
    ("Mathematics", "Statistics", "Maths"),
    ("Mathematics", "Probability", "Maths"),

    # --- SCIENCE (Physics) ---
    ("Science", "Light", "Physics"), # Adjust name based on your PDF index (e.g. "Light - Reflection...")
    ("Science", "Electricity", "Physics"),
    ("Science", "Human Eye", "Physics"),
    ("Science", "Magnetic Effects", "Physics"),

    # --- SCIENCE (Chemistry) ---
    ("Science", "Chemical Reactions and Equations", "Chemistry"),
    ("Science", "Acids, Bases and Salts", "Chemistry"),
]

# Generation Settings
QUESTIONS_PER_BATCH = 4 # 1 MCQ, 1 VSA, 1 SA, 1 LA
BATCHES_PER_CHAPTER = 5 
CASE_STUDIES_PER_CHAPTER = 1
ASSERTION_REASON_PER_CHAPTER = 1 # ✅ New for Section A

gemini = GeminiService()

# ========================================
# VALIDATION
# ========================================
def validate_question(q: Dict) -> bool:
    if not q.get("text") or len(str(q["text"])) < 10: return False
    
    q_type = q.get("question_type", "MCQ")
    
    # MCQ & AR must have options
    if q_type in ["MCQ", "ASSERTION_REASON"]:
        if not q.get("options") or len(q["options"]) < 4: return False
        if not q.get("correctAnswer"): return False
        
    return True

# ========================================
# GENERATORS
# ========================================

async def generate_standard_questions(text: str, meta: Dict) -> List[Dict]:
    """Generates standard questions (MCQ, VSA, SA, LA)"""
    prompt = f"""
    Role: CBSE Exam Question Setter.
    Context from NCERT ({meta.get('subject')} - {meta.get('chapter')}):
    {text[:2000]}

    Task: Create {QUESTIONS_PER_BATCH} high-quality questions based on this context.

    REQUIRED MIX:
    - 1 "MCQ" (1 mark)
    - 1 "VSA" (2 marks)
    - 1 "SA" (3 marks)
    - 1 "LA" (5 marks)

    MCQ FORMAT:
    - Exactly 4 options (A, B, C, D)
    - Clear correct answer

    OUTPUT FORMAT (Valid JSON Array):
    [
      {{
        "text": "Question text...",
        "question_type": "MCQ",
        "options": ["A", "B", "C", "D"],
        "correctAnswer": "A",
        "explanation": "Explanation...",
        "bloomsLevel": "Remember",
        "marks": 1,
        "difficulty": "Easy"
      }},
      {{
        "text": "Explain...",
        "question_type": "SA",
        "options": [],
        "correctAnswer": "Key points...",
        "explanation": "Explanation...",
        "bloomsLevel": "Understand",
        "marks": 3,
        "difficulty": "Medium"
      }}
    ]
    """
    try:
        response = await gemini.generate(prompt, temperature=0.3, max_tokens=3000)
        data = json.loads(repair_json(response))
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"      ⚠️ Standard Gen failed: {str(e)[:50]}...")
        return []

async def generate_assertion_reason_questions(text: str, meta: Dict) -> List[Dict]:
    """Generates Assertion-Reason questions (CBSE 2025-26 Section A)"""
    prompt = f"""
    Role: CBSE Board Exam Setter.
    Context: {text[:1500]}

    Task: Create 1 ASSERTION-REASON question (1 Mark).
    
    Format:
    Assertion (A): [Statement about a concept]
    Reason (R): [Explanation or related statement]
    
    Standard Options (Do not change):
    (a) Both A and R are true and R is the correct explanation of A.
    (b) Both A and R are true but R is not the correct explanation of A.
    (c) A is true but R is false.
    (d) A is false but R is true.
    
    OUTPUT FORMAT (Valid JSON Array):
    [
      {{
        "text": "Assertion (A): ...\\nReason (R): ...",
        "question_type": "ASSERTION_REASON",
        "options": [
            "Both A and R are true and R is the correct explanation of A",
            "Both A and R are true but R is not the correct explanation of A",
            "A is true but R is false",
            "A is false but R is true"
        ],
        "correctAnswer": "Both A and R are true and R is the correct explanation of A", 
        "explanation": "Detailed reasoning...",
        "bloomsLevel": "Analyze",
        "marks": 1,
        "difficulty": "Medium"
      }}
    ]
    """
    try:
        response = await gemini.generate(prompt, temperature=0.4, max_tokens=2000)
        data = json.loads(repair_json(response))
        for q in data: q['question_type'] = "ASSERTION_REASON"
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"      ⚠️ AR Gen failed: {str(e)[:50]}...")
        return []

async def generate_case_study(text: str, meta: Dict) -> List[Dict]:
    """Generates a Case-Based Question (Section E)"""
    prompt = f"""
    Role: CBSE Exam Setter (Case Study Specialist).
    Context: {text[:2000]}
    
    Task: Create 1 CASE-BASED question (4 Marks).
    
    Requirements:
    1. 'text' must be a paragraph (The Case) followed by "Answer the following:".
    2. question_type = "CASE_BASED"
    3. Include 3 sub-questions inside the text or as part of the structure.
    
    OUTPUT FORMAT (Valid JSON Array):
    [
      {{
        "text": "Read the passage: [Case Text]... \\n\\nAnswer: (i) Q1 (ii) Q2 (iii) Q3",
        "question_type": "CASE_BASED",
        "options": [],
        "correctAnswer": "(i) Ans1 (ii) Ans2 (iii) Ans3",
        "explanation": "Detailed analysis",
        "bloomsLevel": "Analyze",
        "marks": 4,
        "difficulty": "Hard"
      }}
    ]
    """
    try:
        response = await gemini.generate(prompt, temperature=0.5, max_tokens=3000)
        data = json.loads(repair_json(response))
        for q in data: q['question_type'] = "CASE_BASED"
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"      ⚠️ Case Gen failed: {str(e)[:50]}...")
        return []

# ========================================
# MAIN SEEDING LOOP
# ========================================

async def seed_chapter(board_subject: str, chapter: str, textbook_subject: str):
    print(f"\n🌱 Seeding: {board_subject} ({textbook_subject}) - {chapter}")
    
    # 1. Fetch Textbooks using TEXTBOOK SUBJECT
    filter_condition = models.Filter(
        must=[
            models.FieldCondition(key="subject", match=models.MatchValue(value=textbook_subject)),
            models.FieldCondition(key="chapter", match=models.MatchValue(value=chapter))
        ]
    )
    
    try:
        # Fetch plenty of chunks to get diverse questions
        results, _ = await qdrant_service.client.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            scroll_filter=filter_condition,
            limit=BATCHES_PER_CHAPTER + CASE_STUDIES_PER_CHAPTER + ASSERTION_REASON_PER_CHAPTER,
            with_payload=True
        )
    except Exception as e:
        print(f"   ❌ Error reading Qdrant: {e}")
        return

    if not results:
        print(f"   ⚠️ No text found for '{chapter}' (Subject: {textbook_subject}). Skipping.")
        return

    print(f"   📖 Found {len(results)} chunks. Generating questions...")
    questions_to_upsert = []

    # 2. Loop through chunks
    for i, point in enumerate(results):
        text = point.payload.get('text', '')
        
        # Determine generator type based on index
        if i < CASE_STUDIES_PER_CHAPTER:
            new_qs = await generate_case_study(text, point.payload)
        elif i < CASE_STUDIES_PER_CHAPTER + ASSERTION_REASON_PER_CHAPTER:
            new_qs = await generate_assertion_reason_questions(text, point.payload)
        else:
            new_qs = await generate_standard_questions(text, point.payload)
        
        # Validate & Enrich
        for q in new_qs:
            if not validate_question(q): continue

            q_text = q.get("text")
            q_type = q.get("question_type", "MCQ")
            
            # METADATA MAPPING (Crucial for Generator)
            q_meta = {
                "text": q_text,
                "question_type": q_type, # ✅ Filter Key
                "type": q_type,
                
                "options": q.get("options", []),
                "correctAnswer": q.get("correctAnswer", ""),
                "explanation": q.get("explanation", ""),
                
                "subject": board_subject,        # ✅ "Science" or "Mathematics"
                "subjectCategory": textbook_subject, # "Physics", "Maths"
                "class_num": 10,                 # ✅ Filter Key
                "class": 10,
                "chapter": chapter,
                "board": "CBSE",
                
                "bloomsLevel": q.get("bloomsLevel", "Understand"),
                "difficulty": q.get("difficulty", "Medium"),
                "marks": q.get("marks", 1),
                
                "sourceTag": "NCERT_AI_GEN_V2",
                "is_validated": True,
                "qualityScore": 0.95,
                "usageCount": 0
            }
            
            questions_to_upsert.append({
                "id": str(uuid.uuid4()),
                "text": q_text,
                "metadata": q_meta
            })
            
        print(f"      Batch {i+1}: +{len(new_qs)} questions")
        # Rate limit pause
        await asyncio.sleep(1)

    # 3. Upsert
    if questions_to_upsert:
        print(f"   💾 Upserting {len(questions_to_upsert)} questions...")
        texts = [q['text'] for q in questions_to_upsert]
        embeddings = gemini.embed_batch(texts)
        
        await qdrant_service.upsert_chunks(
            chunks=questions_to_upsert,
            embeddings=embeddings,
            collection_name=settings.QDRANT_COLLECTION_QUESTIONS
        )
        print(f"   ✅ Done.")
    else:
        print("   ⚠️ No questions generated.")

async def main():
    print("🚀 Starting FINAL DATA SEEDING...")
    await qdrant_service.initialize()
    
    # Optional: Wipe board_questions to ensure no bad data remains?
    # Uncomment next 2 lines if you want a totally fresh start
    # try:
    #     await qdrant_service.client.delete_collection(settings.QDRANT_COLLECTION_QUESTIONS)
    #     await qdrant_service._ensure_question_collection()
    #     print("   🧹 Wiped old questions.")
    # except: pass
    
    for board_sub, chap, text_sub in TARGETS:
        await seed_chapter(board_sub, chap, text_sub)
        
    print("\n🏁 Seeding Complete. Run 'scripts/fix_board_indexes.py' to update filters.")
    await qdrant_service.close()

if __name__ == "__main__":
    asyncio.run(main())