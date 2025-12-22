import os
import requests
from pathlib import Path

# Base NCERT URL pattern: https://ncert.nic.in/textbook/pdf/{book_code}{chapter}.pdf
# Class 10 Science Book Code: jesc1

TARGETS = [
    # --- CBSE Class 10 Science (Physics Chapters) ---
    # Chapter 9: Light – Reflection and Refraction (Rationalized syllabus might differ, usually ch 9 or 10)
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc109.pdf",
        "save_path": "data/textbooks/cbse/class_10_physics_light.pdf"
    },
    # Chapter 10: The Human Eye and the Colorful World
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc110.pdf",
        "save_path": "data/textbooks/cbse/class_10_physics_eye.pdf"
    },
    # Chapter 11: Electricity
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc111.pdf",
        "save_path": "data/textbooks/cbse/class_10_physics_electricity.pdf"
    },
    # Chapter 12: Magnetic Effects of Electric Current
    {
        "url": "https://ncert.nic.in/textbook/pdf/jesc112.pdf",
        "save_path": "data/textbooks/cbse/class_10_physics_magnetic.pdf"
    }
]

def download_file(url, save_path):
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"⬇️  Downloading {url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Saved to {save_path} ({len(response.content)/1024/1024:.2f} MB)")
        else:
            print(f"❌ Failed to download {url} (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error downloading {url}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting PDF Download Sequence...")
    for target in TARGETS:
        download_file(target['url'], target['save_path'])
    print("\n✨ Download sequence complete.")