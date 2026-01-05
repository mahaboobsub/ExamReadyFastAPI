import asyncio
import json
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_exam_generator import LLMExamGenerator
from app.services.pdfgenerator import PDFGenerator
from app.utils.latex_sanitizer import preprocess_exam_json
from dotenv import load_dotenv

load_dotenv()

async def generate_exam_007():
    print("======================================================================")
    print("GENERATING EXAM 007: CHALLENGER")
    print("======================================================================")
    print("Profile: Hard-Heavy (Aim: Easy 29%, Med 47%, Hard 24%)")
    
    generator = LLMExamGenerator()
    start_time = time.time()
    
    # Avoid topics from Exam 005 AND 006 (User provided list)
    avoid_list = [
        # From Exam 005:
        "HCF of 120 and 90", "HCF/LCM with 810", 
        "terminating decimal 3125", "17/6", 
        "x^2-7x+10", "zero of reciprocal",
        "wiper blade angle 115",
        
        # From Exam 006 (User Provided):
        "HCF 18 LCM 540", "29/343 decimal",  # Real Numbers
        "13/1250 terminate 4 places",
        "polynomial x^3-4x+1/2", "zeros sum -b/a",  # Polynomials
        "reciprocal zeros a=c",
        "k=7 infinitely many", "x+2y-5=0 parallel",  # Linear Eq
        "quadratic (x+2)^3=x^3-4", "k=4 equal roots",  # Quadratic
        "AP 2,5,8,11 difference 3",  # AP
        "ladder 4.6m 60 degrees", "tangent √119 cm",  # Trigonometry/Circles
        "fruit vendor 3kg+4kg=180", "ceramic pots 2x+3",  # Word problems
        "bricklayer 35 to 17 bricks",
        "rose bushes 240 and 336"  # Case studies
    ]
    
    try:
        # Generate with 'hard' mode
        exam = await generator.generate_cbse_board_exam(
            board="CBSE",
            class_num=10,
            subject="Mathematics",
            difficulty_mode="hard",  # Bias towards Hard
            avoid_topics=avoid_list
        )
        
        # Save & Sanitize
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # Sanitize matches latex_sanitizer logic
        exam_sanitized = preprocess_exam_json(exam)
        
        sanitized_path = output_dir / "exam_test_007.json"
        with open(sanitized_path, "w", encoding="utf-8") as f:
            json.dump(exam_sanitized, f, indent=2, ensure_ascii=False)
        print(f"✅ Exam 007 saved to {sanitized_path}")
        
        # PDFs
        print("Generating PDFs...")
        pdf_gen = PDFGenerator()
        pdf_gen.output_path = str(output_dir)
        
        pdf_gen.generate_student_pdf("exam_007_CHALLENGER", exam_sanitized)
        pdf_gen.generate_teacher_pdf("exam_007_CHALLENGER", exam_sanitized)
        
        print(f"\nTotal Time: {int(time.time() - start_time)}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_exam_007())
