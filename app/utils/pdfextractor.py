import fitz  # PyMuPDF
from typing import List, Dict, Any
from PIL import Image
import io
import pytesseract
from pix2text import Pix2Text
import os

# WINDOWS CONFIGURATION:
# If 'tesseract' is not in your PATH, uncomment and fix this line:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PDFExtractor:
    """Smart Extractor: Routes images to Pix2Text, Tesseract, or marks for Vision"""

    def __init__(self):
        self.p2t = None # Lazy load

    def _load_p2t(self):
        if not self.p2t:
            print("   ⚙️  Loading Pix2Text model (One-time)...")
            self.p2t = Pix2Text.from_config()
        return self.p2t

    def extract_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        doc = fitz.open(pdf_path)
        pages_data = []

        for page_num, page in enumerate(doc):
            text = page.get_text("text").strip()
            images = []
            
            # Get images
            img_infos = page.get_image_info(xrefs=True)
            
            for i, img_info in enumerate(img_infos):
                # Filter tiny junk
                bbox = img_info['bbox']
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                if width < 100 or height < 50: continue

                try:
                    # Render image
                    pix = page.get_pixmap(clip=bbox, dpi=150)
                    image_bytes = pix.tobytes("png")
                    
                    # --- SMART ROUTING LOGIC ---
                    img_type = "unknown"
                    extracted_text = ""
                    needs_vision = False

                    # 1. Check for Formula (Small, Short)
                    if height < 100 and width < 500:
                        img_type = "formula"
                        # Use Pix2Text
                        try:
                            p2t = self._load_p2t()
                            # recognize returns dict or str
                            res = p2t.recognize(Image.open(io.BytesIO(image_bytes)), resized_shape=500)
                            extracted_text = f"[Formula: {res}]"
                        except:
                            pass # Fallback

                    # 2. Check for Labeled Diagram / Table (Run Tesseract)
                    else:
                        try:
                            ocr_text = pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)))
                            clean_ocr = " ".join(ocr_text.split())
                            
                            # Decision Gate:
                            if len(clean_ocr) > 15: 
                                # Found significant text -> It's a Labeled Diagram or Table
                                img_type = "labeled_diagram"
                                extracted_text = f"[Diagram/Table Labels: {clean_ocr}]"
                            else:
                                # Little/No text -> It's a Pure Diagram -> Needs Vision
                                img_type = "pure_diagram"
                                needs_vision = True
                        except:
                            # OCR Failed -> Fallback to Vision
                            img_type = "pure_diagram"
                            needs_vision = True

                    images.append({
                        "index": i,
                        "bytes": image_bytes,
                        "width": width,
                        "height": height,
                        "type": img_type,
                        "extracted_text": extracted_text,
                        "needs_vision": needs_vision
                    })

                except Exception as e:
                    print(f"⚠️ Error on p{page_num}: {e}")

            pages_data.append({
                "page_num": page_num + 1,
                "text": text,
                "images": images,
                "has_images": len(images) > 0
            })

        doc.close()
        return pages_data