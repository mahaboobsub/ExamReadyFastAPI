"""
Classify extracted questions with CBSE metadata
Uses Gemini to assign chapter, type, difficulty, Bloom's level, section
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.geminiservice import GeminiService


INPUT_FILE = Path("data/processed/questions/all_questions_raw.json")
OUTPUT_FILE = Path("data/processed/questions/all_questions_classified.json")


async def classify_question(question: dict, gemini: GeminiService):
    """
    Use Gemini to classify a single question
    """
    prompt = f"""
Classify this CBSE Class 10 Mathematics question for exam generation.

Question: {question['question_text'][:500]}
Marks: {question.get('marks', 'Unknown')}
Has sub-parts: {question.get('has_sub_parts', False)}

Return ONLY this JSON (no other text):
{{
  "question_type": "MCQ|VSA|SA|LA|Assertion-Reason|Proof|Case Study",
  "difficulty": "Easy|Medium|Hard",
  "blooms_level": "Remember|Understand|Apply|Analyze|Evaluate",
  "section": "A|B|C|D|E",
  "keywords": ["key1", "key2", "key3"]
}}

Classification rules:
- MCQ: Multiple choice, 1 mark
- VSA: Very short answer, 2 marks
- SA: Short answer, 3 marks
- LA: Long answer, 5 marks, usually has sub-parts
- Assertion-Reason: Two statements with relationship
- Proof: "Prove that...", "Show that..."
- Case Study: Multi-part real-world scenario

Section mapping:
- A: MCQ (1 mark)
- B: VSA (2 marks)
- C: SA (3 marks)
- D: LA (5 marks)
- E: Case Study (4 marks)
"""
    
    try:
        response = await gemini.generate(prompt, temperature=0.1, max_tokens=300)
        
        # Clean response
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        # Find JSON object
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start != -1 and end > start:
            json_str = json_str[start:end]
        
        classification = json.loads(json_str)
        
        # Merge with original question
        return {**question, **classification}
        
    except Exception as e:
        print(f"   ⚠️ Classification error: {str(e)[:50]}")
        # Return with defaults
        return {
            **question,
            'question_type': 'SA',
            'difficulty': 'Medium',
            'blooms_level': 'Understand',
            'section': 'C',
            'keywords': []
        }


async def main():
    """
    Main classification pipeline
    """
    print("="*70)
    print("🏷️ QUESTION CLASSIFICATION PIPELINE")
    print("="*70)
    
    # Load raw questions
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run extract_questions_from_pdfs.py first!")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"✅ Loaded {len(questions)} questions from {INPUT_FILE.name}\n")
    
    # Initialize Gemini
    gemini = GeminiService()
    
    # Classify questions
    classified = []
    stats = Counter()
    
    print("📋 Classifying questions...")
    print("-"*70)
    
    for idx, q in enumerate(questions, 1):
        if idx % 10 == 0:
            print(f"   Progress: {idx}/{len(questions)} ({idx/len(questions)*100:.1f}%)")
        
        classified_q = await classify_question(q, gemini)
        classified.append(classified_q)
        
        # Track stats
        stats[classified_q.get('question_type', 'Unknown')] += 1
        
        # Rate limiting
        await asyncio.sleep(0.3)
    
    # Save classified questions
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 CLASSIFICATION SUMMARY")
    print("="*70)
    print(f"Total Questions: {len(classified)}\n")
    
    print("By Question Type:")
    print("-"*70)
    for qtype, count in sorted(stats.items()):
        percentage = (count / len(classified)) * 100
        print(f"  {qtype:<20} {count:>4} ({percentage:>5.1f}%)")
    
    print(f"\n✅ Saved to: {OUTPUT_FILE}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
