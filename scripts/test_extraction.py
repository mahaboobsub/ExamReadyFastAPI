import sys
import os

# Add the project root to python path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.pdfextractor import PDFExtractor

def test_extraction():
    # Use one of the files we downloaded yesterday
    pdf_path = "data/textbooks/cbse/class_10_physics_light.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    print(f"🔍 Analyzing: {pdf_path}...")
    
    extractor = PDFExtractor()
    pages = extractor.extract_pdf(pdf_path)
    
    print(f"✅ Extracted {len(pages)} pages.")
    
    # Analyze Page 1 (usually title/intro)
    first_page = pages[0]
    print(f"\n--- Page 1 Preview ---")
    print(f"Text length: {len(first_page['text'])} chars")
    print(f"Text snippet: {first_page['text'][:200]}...")
    
    # Analyze Image Detection Statistics
    total_images = sum(len(p['images']) for p in pages)
    formulas = 0
    diagrams = 0
    
    for p in pages:
        for img in p['images']:
            if extractor.is_formula_image(img['bytes']):
                formulas += 1
            elif extractor.is_diagram(img['bytes']):
                diagrams += 1
                
    print(f"\n--- Image Analysis ---")
    print(f"Total Images Found: {total_images}")
    print(f"Likely Formulas: {formulas}")
    print(f"Likely Diagrams: {diagrams}")
    print(f"Unclassified: {total_images - formulas - diagrams}")

if __name__ == "__main__":
    test_extraction()