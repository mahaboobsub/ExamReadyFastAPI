import sys
import os
from PIL import Image
import io

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.pdfextractor import PDFExtractor
from app.services.visionservice import VisionService

def test_vision_pipeline():
    pdf_path = "data/textbooks/cbse/class_10_physics_light.pdf"
    
    print("1️⃣  Extracting images from PDF...")
    extractor = PDFExtractor()
    pages = extractor.extract_pdf(pdf_path)
    
    # Scan pages 5 to 15 (Diagrams definitely exist here in Chapter 9)
    target_pages = pages[4:15] 
    
    candidate_image = None
    
    print(f"   Scanning pages 5-15 for valid diagrams...")
    
    for page in target_pages:
        if page['images']:
            for img in page['images']:
                w, h = img['width'], img['height']
                
                # --- SMARTER FILTER ---
                # 1. Skip tiny icons (width < 200)
                # 2. Skip full-page background masks (width > 2000) - THIS WAS THE ISSUE
                # 3. Skip extremely thin lines (aspect ratio > 5)
                
                if (200 < w < 2000) and (200 < h < 2000):
                    aspect = w / h
                    if 0.3 < aspect < 3.0: # reasonably square/rectangular
                        candidate_image = img
                        print(f"✅ Found content image on Page {page['page_num']} ({w}x{h})")
                        break # Stop at the first good one
        
        if candidate_image:
            break
            
    if not candidate_image:
        print("❌ No suitable diagrams found. The PDF might parse images differently.")
        return

    # DEBUG: Save the image so YOU can see it
    debug_path = "debug_vision_test.png"
    with open(debug_path, "wb") as f:
        f.write(candidate_image['bytes'])
    print(f"💾 Saved debug image to: {debug_path} (Open this file to verify it's not black!)")

    print("2️⃣  Sending to Gemini Vision...")
    vision = VisionService()
    
    description = vision.describe_diagram(candidate_image['bytes'])
    
    print("\n--- 🤖 AI Description ---")
    print(description)
    print("-------------------------")

if __name__ == "__main__":
    test_vision_pipeline()