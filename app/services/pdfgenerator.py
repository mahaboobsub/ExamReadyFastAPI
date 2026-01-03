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

    def generate_student_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Generates Student Exam PDF (Questions Only)"""
        student_template = self.template_env.get_template("exam_pdf.html")
        student_html = student_template.render(exam=exam_data)
        filename = f"{exam_id}_student.pdf"
        path = os.path.join(self.output_path, filename)
        HTML(string=student_html).write_pdf(path)
        print(f"[PDF] ✅ Generated Student Exam: {path}")
        return path

    def generate_teacher_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Generates Teacher Answer Key PDF (With Solutions)"""
        teacher_template = self.template_env.get_template("answer_key_pdf.html")
        teacher_html = teacher_template.render(exam=exam_data)
        filename = f"{exam_id}_teacher_key.pdf"
        path = os.path.join(self.output_path, filename)
        HTML(string=teacher_html).write_pdf(path)
        print(f"[PDF] ✅ Generated Answer Key: {path}")
        return path
        
    def generate_exam_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Alias for student pdf for backward compatibility"""
        return self.generate_student_pdf(exam_id, exam_data)

pdf_generator = PDFGenerator()