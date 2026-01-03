"""
Enhanced PDF Extractor with OCR, Formula Detection, and Content Classification
Integrates: PyMuPDF + pix2text + Tesseract + Gemini Vision
"""
import os
import re
import io
from typing import List, Dict, Any, Optional
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    import pymupdf as fitz

from .hindi_remover import remove_hindi_text, contains_hindi
from .solution_detector import detect_content_type, is_likely_marking_scheme_file


class PDFProcessor:
    """
    Smart PDF Processor that routes content through appropriate extraction methods:
    - Plain text: PyMuPDF
    - Formulas: pix2text
    - Labeled diagrams: Tesseract OCR
    - Pure diagrams: Gemini Vision (optional)
    """
    
    def __init__(self, use_ocr: bool = True, use_vision: bool = False):
        """
        Initialize PDF Processor
        
        Args:
            use_ocr: Enable OCR for images (requires pix2text, tesseract)
            use_vision: Enable Gemini Vision for pure diagrams
        """
        self.use_ocr = use_ocr
        self.use_vision = use_vision
        self.p2t = None
        
        if use_ocr:
            self._init_ocr()
    
    def _init_ocr(self):
        """Lazy load pix2text model"""
        try:
            from pix2text import Pix2Text
            print("   ⚙️ Loading Pix2Text model...")
            self.p2t = Pix2Text.from_config()
        except ImportError:
            print("   ⚠️ pix2text not installed, formula OCR disabled")
            self.p2t = None
        except Exception as e:
            print(f"   ⚠️ Failed to load pix2text: {e}")
            self.p2t = None
    
    def extract_pdf(self, pdf_path: str, remove_hindi: bool = True) -> List[Dict[str, Any]]:
        """
        Extract text and images from PDF with smart content classification
        
        Args:
            pdf_path: Path to PDF file
            remove_hindi: Whether to remove Hindi text from question pages
            
        Returns:
            List of page dictionaries with text, images, and metadata
        """
        doc = fitz.open(pdf_path)
        pages_data = []
        
        # Check if file is likely a marking scheme
        is_ms_file = is_likely_marking_scheme_file(os.path.basename(pdf_path))
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract raw text
            raw_text = page.get_text("text").strip()
            
            # Detect content type
            if is_ms_file:
                content_type = "solution"
            else:
                content_type = detect_content_type(raw_text, page_num)
            
            # Process text based on content type
            if content_type == "question" and remove_hindi:
                processed_text = remove_hindi_text(raw_text)
            else:
                processed_text = raw_text
            
            # Extract and process images if OCR enabled
            images_data = []
            if self.use_ocr:
                images_data = self._extract_images(page, page_num)
                
                # Append image text to page text
                for img in images_data:
                    if img.get('extracted_text'):
                        processed_text += f"\n\n{img['extracted_text']}"
            
            # Skip nearly empty pages
            if len(processed_text.strip()) < 30:
                continue
            
            pages_data.append({
                "page_num": page_num + 1,
                "text": processed_text,
                "raw_text": raw_text,
                "content_type": content_type,
                "has_images": len(images_data) > 0,
                "images": images_data,
                "hindi_removed": content_type == "question" and remove_hindi and contains_hindi(raw_text)
            })
        
        doc.close()
        return pages_data
    
    def _extract_images(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract and process images from a page
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of image data dictionaries
        """
        images = []
        
        try:
            img_infos = page.get_image_info(xrefs=True)
        except:
            return images
        
        for i, img_info in enumerate(img_infos):
            try:
                # Get bounding box
                bbox = img_info.get('bbox', [0, 0, 0, 0])
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                # Skip tiny images (likely decorative)
                if width < 80 or height < 40:
                    continue
                
                # Render image region
                pix = page.get_pixmap(clip=bbox, dpi=150)
                image_bytes = pix.tobytes("png")
                
                # Classify and process image
                img_type, extracted_text, needs_vision = self._process_image(
                    image_bytes, width, height
                )
                
                images.append({
                    "index": i,
                    "width": width,
                    "height": height,
                    "type": img_type,
                    "extracted_text": extracted_text,
                    "needs_vision": needs_vision,
                    "bytes": image_bytes if needs_vision else None
                })
                
            except Exception as e:
                print(f"   ⚠️ Error extracting image {i} on page {page_num}: {e}")
        
        return images
    
    def _process_image(self, image_bytes: bytes, width: float, height: float) -> tuple:
        """
        Process image and extract text using appropriate method
        
        Args:
            image_bytes: PNG image bytes
            width: Image width
            height: Image height
            
        Returns:
            Tuple of (img_type, extracted_text, needs_vision)
        """
        img_type = "unknown"
        extracted_text = ""
        needs_vision = False
        
        # Small images are likely formulas
        if height < 100 and width < 500 and self.p2t:
            img_type = "formula"
            try:
                img = Image.open(io.BytesIO(image_bytes))
                result = self.p2t.recognize(img, resized_shape=500)
                if isinstance(result, dict):
                    extracted_text = f"[Formula: {result.get('text', str(result))}]"
                else:
                    extracted_text = f"[Formula: {result}]"
            except Exception as e:
                print(f"      ⚠️ pix2text error: {e}")
        
        # Larger images - try Tesseract OCR
        else:
            try:
                import pytesseract
                img = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(img)
                clean_ocr = " ".join(ocr_text.split())
                
                if len(clean_ocr) > 15:
                    # Found significant text - labeled diagram or table
                    img_type = "labeled_diagram"
                    extracted_text = f"[Diagram/Table: {clean_ocr}]"
                else:
                    # Little/no text - pure diagram
                    img_type = "pure_diagram"
                    needs_vision = self.use_vision
                    
            except ImportError:
                img_type = "pure_diagram"
                needs_vision = self.use_vision
            except Exception as e:
                img_type = "pure_diagram"
                needs_vision = self.use_vision
        
        return img_type, extracted_text, needs_vision


def extract_pdf_with_metadata(
    pdf_path: str,
    remove_hindi: bool = True,
    use_ocr: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract PDF with metadata
    
    Args:
        pdf_path: Path to PDF file
        remove_hindi: Whether to remove Hindi from question pages
        use_ocr: Whether to use OCR for images
        
    Returns:
        List of page dictionaries
    """
    processor = PDFProcessor(use_ocr=use_ocr, use_vision=False)
    return processor.extract_pdf(pdf_path, remove_hindi=remove_hindi)
