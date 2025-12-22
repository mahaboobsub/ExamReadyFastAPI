import fitz  # PyMuPDF
import re

def test_physics_formulas():
    # Target: Class 10 Physics - Light Chapter
    pdf_path = "data/textbooks/cbse/class_10_physics_light.pdf"
    
    print(f"🔍 Inspecting: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    # We look for common optical formulas expected in this chapter
    # 1. Mirror Formula: 1/v + 1/u = 1/f
    # 2. Magnification: m = h'/h
    # 3. Snell's Law: sin i / sin r
    # 4. Power of lens: P = 1/f
    
    hits = {
        "mirror_formula": 0,
        "magnification": 0,
        "snells_law": 0,
        "power_lens": 0
    }
    
    print("\n--- Scanning Text Layer for Math ---")
    
    for page in doc:
        text = page.get_text("text")
        
        # Normalize whitespace for matching
        clean_text = " ".join(text.split())
        
        # Check patterns (relaxed matching)
        if "1/v" in clean_text and "1/u" in clean_text:
            hits["mirror_formula"] += 1
            print(f"✅ Found Mirror Formula candidate on Page {page.number + 1}")
            print(f"   Context: ...{clean_text[clean_text.find('1/v')-20 : clean_text.find('1/v')+30]}...\n")
            
        if "h'/h" in clean_text or "h’/h" in clean_text: # Check both quote types
            hits["magnification"] += 1
            
        if "sin i" in clean_text and "sin r" in clean_text:
            hits["snells_law"] += 1
            
        if "P = 1/f" in clean_text or "P=1/f" in clean_text:
            hits["power_lens"] += 1

    print("-" * 30)
    print("RESULTS:")
    print(f"Mirror Formula (1/v + 1/u): found {hits['mirror_formula']} times")
    print(f"Magnification (h'/h):       found {hits['magnification']} times")
    print(f"Snell's Law (sin i/sin r):  found {hits['snells_law']} times")
    print(f"Power (P = 1/f):            found {hits['power_lens']} times")
    print("-" * 30)

    if sum(hits.values()) > 5:
        print("🎉 SCENARIO A: Text Layer is GOOD! (No Pix2Text needed)")
    else:
        print("⚠️ SCENARIO B: Text Layer is WEAK. (Formulas are images/garbled)")

if __name__ == "__main__":
    test_physics_formulas()