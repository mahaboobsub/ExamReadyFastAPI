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

async def generate_exam_006():
    print("======================================================================")
    print("GENERATING EXAM 006: CONFIDENCE BUILDER (RETRY - ROBUST)")
    print("======================================================================")
    print("Profile: Easy-Heavy")
    print("Avoid Topics: HCF 810, Terminating 3125, x^2-7x+10")
    
    # Clean up old files
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    for f in ["exam_test_006.json", "exam_test_006_raw.json"]:
        p = output_dir / f
        if p.exists():
            print(f"Removing old {f}...")
            p.unlink()

    generator = LLMExamGenerator()
    
    start_time = time.time()
    
    # Avoid topics from Exam 005 to ensure uniqueness
    avoid_list = [
        "HCF of 120 and 90", "HCF/LCM with 810", 
        "terminating decimal 3125", "17/6", 
        "x^2-7x+10", "zero of reciprocal",
        "wiper blade angle 115"
    ]
    
    try:
        # Generate with 'easy' mode
        exam = await generator.generate_cbse_board_exam(
            board="CBSE",
            class_num=10,
            subject="Mathematics",
            difficulty_mode="easy",  # Bias towards Easy/Medium
            avoid_topics=avoid_list
        )
        
        # Save Raw JSON
        raw_path = output_dir / "exam_test_006_raw.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(exam, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Raw Exam saved to {raw_path}")
        
        # Sanitize LaTeX
        print("Sanitizing LaTeX...")
        exam_sanitized = preprocess_exam_json(exam)
        
        sanitized_path = output_dir / "exam_test_006.json"
        with open(sanitized_path, "w", encoding="utf-8") as f:
            json.dump(exam_sanitized, f, indent=2, ensure_ascii=False)
        print(f"✅ Sanitized Exam saved to {sanitized_path}")
        
        # Validate Size check (Rough heuristic)
        size_kb = sanitized_path.stat().st_size / 1024
        print(f"File Size: {size_kb:.2f} KB (Expected ~80 KB)")
        if size_kb < 50:
            print("⚠️ WARNING: File seems too small. Generation might be incomplete.")
        
        # Generate PDFs
        print("Generating PDFs...")
        pdf_gen = PDFGenerator()
        pdf_gen.output_path = str(output_dir)
        
        student_pdf = pdf_gen.generate_student_pdf("exam_006_CONFIDENCE", exam_sanitized)
        teacher_pdf = pdf_gen.generate_teacher_pdf("exam_006_CONFIDENCE", exam_sanitized)
        
        print(f"✅ Student PDF: {student_pdf}")
        print(f"✅ Teacher PDF: {teacher_pdf}")
        
        print(f"\nTotal Time: {int(time.time() - start_time)}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_exam_006())
