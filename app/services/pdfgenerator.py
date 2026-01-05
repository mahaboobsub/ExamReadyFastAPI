from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Dict, Tuple
import os
import uuid
import logging
import traceback
from app.config.settings import settings

logger = logging.getLogger("examready")

class PDFGenerator:
    """Generate exam PDFs using Jinja2 templates and WeasyPrint"""
    
    def __init__(self):
        self.output_path = settings.OUTPUT_PDF_PATH
        self.template_env = Environment(loader=FileSystemLoader("app/templates"))
        os.makedirs(self.output_path, exist_ok=True)

    def generate_student_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Generates Student Exam PDF (Questions Only) with robust error handling"""
        try:
            student_template = self.template_env.get_template("exam_pdf.html")
            student_html = student_template.render(exam=exam_data)
            
            filename = f"{exam_id}_student.pdf"
            path = os.path.join(self.output_path, filename)
            
            try:
                HTML(string=student_html).write_pdf(path)
            except Exception as pdf_error:
                # Save HTML for debugging
                debug_path = path.replace(".pdf", "_debug.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(student_html)
                
                logger.error(f"PDF conversion failed. Debug HTML saved to {debug_path}")
                logger.error(f"PDF Error: {pdf_error}")
                logger.error(traceback.format_exc())
                raise Exception(f"PDF generation failed. Debug HTML: {debug_path}")
            
            print(f"[PDF] ✅ Generated Student Exam: {path}")
            return path
            
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise Exception(f"PDF template not found: exam_pdf.html")
        except Exception as e:
            logger.error(f"Unexpected PDF error: {e}")
            logger.error(traceback.format_exc())
            raise

    def generate_teacher_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Generates Teacher Answer Key PDF (With Solutions) with robust error handling"""
        try:
            teacher_template = self.template_env.get_template("answer_key_pdf.html")
            teacher_html = teacher_template.render(exam=exam_data)
            
            filename = f"{exam_id}_teacher_key.pdf"
            path = os.path.join(self.output_path, filename)
            
            try:
                HTML(string=teacher_html).write_pdf(path)
            except Exception as pdf_error:
                # Save HTML for debugging
                debug_path = path.replace(".pdf", "_debug.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(teacher_html)
                
                logger.error(f"Answer key PDF failed. Debug HTML saved to {debug_path}")
                logger.error(f"PDF Error: {pdf_error}")
                logger.error(traceback.format_exc())
                raise Exception(f"Answer key PDF failed. Debug HTML: {debug_path}")
            
            print(f"[PDF] ✅ Generated Answer Key: {path}")
            return path
            
        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise Exception(f"PDF template not found: answer_key_pdf.html")
        except Exception as e:
            logger.error(f"Unexpected PDF error: {e}")
            logger.error(traceback.format_exc())
            raise
        
    def generate_exam_pdf(self, exam_id: str, exam_data: Dict) -> str:
        """Alias for student pdf for backward compatibility"""
        return self.generate_student_pdf(exam_id, exam_data)

pdf_generator = PDFGenerator()