import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pdfgenerator import PDFGenerator
from app.config.settings import settings

from app.utils.latex_sanitizer import preprocess_exam_json

def finalize_exam():
    # 1. Load Exam 005
    input_path = Path("test_output/exam_test_005.json")
    print(f"Loading {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        exam = json.load(f)
    
    # 2. Patch Q17 in Section A
    print("Patching Section A Q17...")
    section_a = exam['sections']['A']['questions']
    patched = False
    
    # Try finding by text first
    for i, q in enumerate(section_a):
        if "wiper" in q['text'].lower():
            print(f"  Found Q{i+1}: {q['text'][:50]}...")
            print(f"  Old Chapter: {q.get('chapter')}")
            q['chapter'] = "Areas Related to Circles"
            print(f"  New Chapter: {q['chapter']}")
            patched = True
            break
            
    if not patched:
        # Fallback to index 16 (17th question)
        if len(section_a) > 16:
            q = section_a[16]
            print(f"  Fallback to Index 16: {q['text'][:50]}...")
            q['chapter'] = "Areas Related to Circles"
            patched = True
    
    if patched:
        # Save patched version
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(exam, f, indent=2, ensure_ascii=False)
        print("✅ Exam JSON patched successfully.")
    else:
        print("⚠️ Could not find Q17 to patch!")

    # 3. Sanitize LaTeX for PDF
    print("Sanitizing LaTeX for PDF generation...")
    exam_sanitized = preprocess_exam_json(exam)

    # 4. Generate PDFs
    print("\nGenerating PDFs...")
    pdf_gen = PDFGenerator()
    
    # Ensure output dir exists
    output_dir = Path("test_output")
    pdf_gen.output_path = str(output_dir) # Override output path to test_output
    
    # Generate Student PDF
    student_pdf = pdf_gen.generate_student_pdf(
        exam_id="exam_005_OFFICIAL",
        exam_data=exam_sanitized  # Use sanitized data
    )
    print(f"✅ Student PDF: {student_pdf}")
    
    
    # Generate Teacher PDF
    teacher_pdf = pdf_gen.generate_teacher_pdf(
        exam_id="exam_005_OFFICIAL",
        exam_data=exam_sanitized
    )
    print(f"✅ Teacher Key PDF: {teacher_pdf}")
    
if __name__ == "__main__":
    finalize_exam()
