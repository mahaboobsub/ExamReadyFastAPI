"""
ExamReady PDF Processor Module
Handles: Hindi removal, Solution detection, OCR, Qdrant storage
"""
from .pdf_extractor import extract_pdf_with_metadata, PDFProcessor
from .hindi_remover import remove_hindi_text, contains_hindi
from .solution_detector import detect_content_type, SOLUTION_KEYWORDS
from .pyq_processor import PYQProcessor

__all__ = [
    'PDFProcessor',
    'PYQProcessor',
    'extract_pdf_with_metadata',
    'remove_hindi_text',
    'contains_hindi',
    'detect_content_type',
    'SOLUTION_KEYWORDS'
]
