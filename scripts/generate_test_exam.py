import asyncio
import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_exam_generator import LLMExamGenerator
from app.services.qdrant_service import qdrant_service

async def generate_test_exam():
    """
    Generate a single CBSE Class 10 Mathematics exam for validation
    This tests paper reliability and accuracy (not deduplication)
    """
    print("="*70)
    print("GENERATING TEST EXAM - CBSE Class 10 Mathematics")
    print("="*70)
    
    # Initialize Qdrant (needed for RAG context)
    await qdrant_service.initialize()
    
    generator = LLMExamGenerator()
    
    # All 14 chapters (MANDATORY)
    chapters = [
        "Real Numbers", "Polynomials", 
        "Pair of Linear Equations in Two Variables",
        "Quadratic Equations", "Arithmetic Progressions",
        "Triangles", "Coordinate Geometry",
        "Introduction to Trigonometry", "Some Applications of Trigonometry",
        "Circles", "Areas Related to Circles",
        "Surface Areas and Volumes", "Statistics", "Probability"
    ]
    
    print(f"\nTarget: All {len(chapters)} chapters")
    print("Expected: 38 questions, 80 marks, 5 sections (A-E)")
    print("\nStarting generation...\n")
    
    try:
        exam = await generator.generate_cbse_board_exam(
            board="CBSE",
            class_num=10,
            subject="Mathematics",
            chapters=chapters
        )
        
        # Save to file
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / "exam_test_005.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(exam, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*70)
        print("GENERATION COMPLETE")
        print("="*70)
        print(f"Exam saved to: {output_path}")
        print(f"\nQuick Stats:")
        print(f"  Total Questions: {exam['metadata']['totalQuestions']}")
        print(f"  Total Marks: {exam['metadata']['totalMarks']}")
        print(f"  Generation Time: {exam['metadata']['generationTimeMs']}ms")
        print(f"  Sections: {len(exam['sections'])}")
        
        for code, section in exam['sections'].items():
            q_count = len(section.get('questions', []))
            marks = section.get('marks', 0)
            print(f"    Section {code}: {q_count} questions, {marks} marks")
        
        # Quick validation checks
        print("\n" + "-"*70)
        print("QUICK VALIDATION CHECKS")
        print("-"*70)
        
        total_q = exam['metadata']['totalQuestions']
        total_m = exam['metadata']['totalMarks']
        
        # Check totals
        print(f"  [{'✅' if total_q == 38 else '❌'}] Total Questions: {total_q}/38")
        print(f"  [{'✅' if total_m == 80 else '❌'}] Total Marks: {total_m}/80")
        print(f"  [{'✅' if len(exam['sections']) == 5 else '❌'}] Sections: {len(exam['sections'])}/5")
        
        # Check for mock questions
        all_questions = []
        for section in exam['sections'].values():
            all_questions.extend(section.get('questions', []))
        
        mock_count = sum(1 for q in all_questions if '[MOCK]' in q.get('text', ''))
        print(f"  [{'✅' if mock_count == 0 else '❌'}] Mock Questions: {mock_count} (should be 0)")
        
        # Chapter coverage
        chapters_found = set()
        for q in all_questions:
            ch = q.get('chapter', '')
            if ch:
                chapters_found.add(ch)
        print(f"  [{'✅' if len(chapters_found) >= 12 else '⚠️'}] Chapters Covered: {len(chapters_found)}/14")
        
        print("\n" + "="*70)
        print(f"✅ Next step: Review {output_path} for detailed validation")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await qdrant_service.close()

if __name__ == "__main__":
    asyncio.run(generate_test_exam())
