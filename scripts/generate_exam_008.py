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

async def generate_exam_008():
    print("======================================================================")
    print("GENERATING EXAM 008: BOARD SIMULATOR")
    print("======================================================================")
    print("Profile: Balanced (Aim: Easy 34%, Med 50%, Hard 16%)")
    
    generator = LLMExamGenerator()
    start_time = time.time()
    
    # Avoid topics from previous exams (005, 006, 007)
    avoid_list = [
        # Exam 005
        "HCF of 120 and 90", "HCF/LCM with 810", 
        "terminating decimal 3125", "17/6", 
        "x^2-7x+10", "zero of reciprocal",
        "wiper blade angle 115",
        
        # Exam 006
        "HCF 18 LCM 540", "29/343 decimal",
        "13/1250 terminate 4 places",
        "polynomial x^3-4x+1/2", "zeros sum -b/a",
        "reciprocal zeros a=c", "k=7 infinitely many",
        "quadratic (x+2)^3=x^3-4", "k=4 equal roots",
        "AP 2,5,8,11 difference 3",
        "ladder 4.6m 60 degrees", "tangent √119 cm",
        "fruit vendor 3kg+4kg=180", "ceramic pots 2x+3",
        "bricklayer 35 to 17 bricks", "rose bushes 240 and 336",
        
        # Exam 007 (Extracted)
        "13/320 terminating", "LCM 144 product 576", 
        "6^n digit 0", "sum zeroes 4 product -5",
        "sum rational x irrational y always irrational", "Dr. Arya real numbers",
        "cubic polynomial zeroes in AP 1,2,3", "coefficients A=-6 B=11",
        "bakery blueberry chocolate chip muffins", "flour 1.95kg sugar 1.2kg",
        "school canteen fruit baskets 252 324", "apple banana juice boxes",
        "pedestrian bridge parabolic arch", "h(x)=-x^2+8x-12"
    ]
    
    try:
        # Generate with 'standard' mode
        exam = await generator.generate_cbse_board_exam(
            board="CBSE",
            class_num=10,
            subject="Mathematics",
            difficulty_mode="standard",  # Balanced
            avoid_topics=avoid_list
        )
        
        # Save & Sanitize
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        exam_sanitized = preprocess_exam_json(exam)
        
        sanitized_path = output_dir / "exam_test_008.json"
        with open(sanitized_path, "w", encoding="utf-8") as f:
            json.dump(exam_sanitized, f, indent=2, ensure_ascii=False)
        print(f"✅ Exam 008 saved to {sanitized_path}")
        
        # PDFs
        print("Generating PDFs...")
        pdf_gen = PDFGenerator()
        pdf_gen.output_path = str(output_dir)
        
        pdf_gen.generate_student_pdf("exam_008_BOARDSIM", exam_sanitized)
        pdf_gen.generate_teacher_pdf("exam_008_BOARDSIM", exam_sanitized)
        
        print(f"\nTotal Time: {int(time.time() - start_time)}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_exam_008())
