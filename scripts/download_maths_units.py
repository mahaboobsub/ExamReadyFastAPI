import os
import requests
from pathlib import Path

# NCERT Class 10 Maths (Book Code: jemh1)
# Ch 1: Real Numbers (jemh101)
# Ch 2: Polynomials (jemh102)

UNITS = [
    {
        "url": "https://ncert.nic.in/textbook/pdf/jemh101.pdf",
        "filename": "class_10_maths_ch1.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Maths", "chapter": "Real Numbers"}
    },
    {
        "url": "https://ncert.nic.in/textbook/pdf/jemh102.pdf",
        "filename": "class_10_maths_ch2.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Maths", "chapter": "Polynomials"}
    }
]

DATA_DIR = "data/textbooks/cbse"

def download_units():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"📐 Starting Maths Unit Download...")
    
    for unit in UNITS:
        save_path = os.path.join(DATA_DIR, unit['filename'])
        
        if os.path.exists(save_path):
            print(f"   ✅ Already exists: {unit['filename']}")
            continue
            
        print(f"   ⬇️  Downloading {unit['metadata']['chapter']}...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(unit['url'], headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✅ Saved to {save_path}")
        except Exception as e:
            print(f"   ❌ Failed to download {unit['url']}: {e}")

    print("\n📦 Download Complete. Ready for Indexing.")

if __name__ == "__main__":
    download_units()