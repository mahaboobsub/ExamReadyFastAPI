"""
Download NCERT Class 10 Mathematics Textbook PDFs
All 14 chapters from ncert.nic.in
"""
import requests
import os
from pathlib import Path

OUTPUT_DIR = "data/textbooks/class_10/mathematics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# NCERT Class 10 Mathematics Chapters (jemh = Junior English Medium Higher - Maths)
CHAPTERS = {
    "jemh101.pdf": ("Chapter 1: Real Numbers", "https://ncert.nic.in/textbook/pdf/jemh101.pdf"),
    "jemh102.pdf": ("Chapter 2: Polynomials", "https://ncert.nic.in/textbook/pdf/jemh102.pdf"),
    "jemh103.pdf": ("Chapter 3: Pair of Linear Equations", "https://ncert.nic.in/textbook/pdf/jemh103.pdf"),
    "jemh104.pdf": ("Chapter 4: Quadratic Equations", "https://ncert.nic.in/textbook/pdf/jemh104.pdf"),
    "jemh105.pdf": ("Chapter 5: Arithmetic Progressions", "https://ncert.nic.in/textbook/pdf/jemh105.pdf"),
    "jemh106.pdf": ("Chapter 6: Triangles", "https://ncert.nic.in/textbook/pdf/jemh106.pdf"),
    "jemh107.pdf": ("Chapter 7: Coordinate Geometry", "https://ncert.nic.in/textbook/pdf/jemh107.pdf"),
    "jemh108.pdf": ("Chapter 8: Introduction to Trigonometry", "https://ncert.nic.in/textbook/pdf/jemh108.pdf"),
    "jemh109.pdf": ("Chapter 9: Applications of Trigonometry", "https://ncert.nic.in/textbook/pdf/jemh109.pdf"),
    "jemh110.pdf": ("Chapter 10: Circles", "https://ncert.nic.in/textbook/pdf/jemh110.pdf"),
    "jemh111.pdf": ("Chapter 11: Areas Related to Circles", "https://ncert.nic.in/textbook/pdf/jemh111.pdf"),
    "jemh112.pdf": ("Chapter 12: Surface Areas and Volumes", "https://ncert.nic.in/textbook/pdf/jemh112.pdf"),
    "jemh113.pdf": ("Chapter 13: Statistics", "https://ncert.nic.in/textbook/pdf/jemh113.pdf"),
    "jemh114.pdf": ("Chapter 14: Probability", "https://ncert.nic.in/textbook/pdf/jemh114.pdf"),
}


def download_chapter(filename: str, name: str, url: str) -> bool:
    """Download a single chapter"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"   ⏭️ Already exists: {filename} ({size_kb:.2f} KB)")
        return True
    
    try:
        print(f"\n📥 Downloading: {name}")
        print(f"   URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf',
        }
        
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_kb = os.path.getsize(filepath) / 1024
            print(f"   ✅ Downloaded: {size_kb:.2f} KB")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("📚 NCERT CLASS 10 MATHEMATICS TEXTBOOK DOWNLOADER")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Total chapters: {len(CHAPTERS)}")
    
    success = 0
    failed = 0
    
    for filename, (name, url) in CHAPTERS.items():
        if download_chapter(filename, name, url):
            success += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"✅ Downloaded: {success}/{len(CHAPTERS)}")
    print(f"❌ Failed: {failed}")
    print("="*60)
    
    if failed > 0:
        print("\n💡 Manual Download:")
        print("   Visit: https://ncert.nic.in/textbook.php?jemh1=0-14")
        print("   Click on each chapter to download")
        print(f"   Save to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
