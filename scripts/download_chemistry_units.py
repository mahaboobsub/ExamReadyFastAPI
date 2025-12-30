import os
import requests
from pathlib import Path

# NCERT Class 10 Science (Book Code: jesc1)
# Ch 1: Chemical Reactions (jesc101)
# Ch 2: Acids, Bases and Salts (jesc102)

UNITS = [
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc101.pdf",
        "filename": "class_10_chemistry_ch1.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Chemistry", "chapter": "Chemical Reactions and Equations"}
    },
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc102.pdf",
        "filename": "class_10_chemistry_ch2.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Chemistry", "chapter": "Acids, Bases and Salts"}
    }
]

DATA_DIR = "data/textbooks/cbse"

def download_units():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"🧪 Starting Chemistry Unit Download...")
    
    for unit in UNITS:
        save_path = os.path.join(DATA_DIR, unit['filename'])
        
        # Don't re-download if exists
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