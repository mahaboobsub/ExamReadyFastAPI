from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Tuple
import os
import uuid
from app.config.settings import settings

class PDFGenerator:
    """Generate exam PDFs using Jinja2 templates and WeasyPrint"""
    
    def __init__(self):
        self.output_path = settings.OUTPUT_PDF_PATH
        self.template_env = Environment(loader=FileSystemLoader("app/templates"))
        os.makedirs(self.output_path, exist_ok=True)

    def generate_dual_pdfs(self, exam_data: Dict) -> Tuple[str, str]:
        """
        Generates both Student Exam PDF and Teacher Answer Key PDF.
        Returns: Tuple[str, str]: (student_filename, teacher_filename)
        """
        exam_id = exam_data.get("exam_id", str(uuid.uuid4()))
        
        # 1. Student PDF
        student_template = self.template_env.get_template("exam_pdf.html")
        student_html = student_template.render(exam=exam_data)
        student_filename = f"{exam_id}_student.pdf"
        student_path = os.path.join(self.output_path, student_filename)
        HTML(string=student_html).write_pdf(student_path)
        print(f"[PDF] ✅ Generated Student Exam: {student_path}")

        # 2. Answer Key PDF
        teacher_template = self.template_env.get_template("answer_key_pdf.html")
        teacher_html = teacher_template.render(exam=exam_data)
        teacher_filename = f"{exam_id}_teacher_key.pdf"
        teacher_path = os.path.join(self.output_path, teacher_filename)
        HTML(string=teacher_html).write_pdf(teacher_path)
        print(f"[PDF] ✅ Generated Answer Key: {teacher_path}")

        # ✅ Return FILENAMES ONLY
        return student_filename, teacher_filename

pdf_generator = PDFGenerator()