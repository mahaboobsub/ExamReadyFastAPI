"""
Download CBSE Sample Papers for Class 10 Mathematics (2025-26)
"""
import requests
import os
from pathlib import Path

# Create directory
OUTPUT_DIR = "data/sample_papers/class_10/mathematics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Official CBSE Sample Papers 2025-26
# Note: URLs may need to be updated based on cbseacademic.nic.in
SAMPLE_PAPERS = {
    "CBSE_Class10_Maths_Standard_SQP_2026.pdf": 
        "https://cbseacademic.nic.in/web_material/SQP/ClassX_2024_25/Mathematics_Standard_SQP.pdf",
    
    "CBSE_Class10_Maths_Standard_MS_2026.pdf": 
        "https://cbseacademic.nic.in/web_material/SQP/ClassX_2024_25/Mathematics_Standard_MS.pdf",
    
    "CBSE_Class10_Maths_Basic_SQP_2026.pdf": 
        "https://cbseacademic.nic.in/web_material/SQP/ClassX_2024_25/Mathematics_Basic_SQP.pdf",
    
    "CBSE_Class10_Maths_Basic_MS_2026.pdf": 
        "https://cbseacademic.nic.in/web_material/SQP/ClassX_2024_25/Mathematics_Basic_MS.pdf",
}


def download_file(url: str, filename: str):
    """Download file with progress"""
    try:
        print(f"\n📥 Downloading: {filename}")
        print(f"   URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        
        if response.status_code == 200:
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath) / 1024  # KB
            print(f"   ✅ Downloaded: {file_size:.2f} KB")
            return True
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("📥 CBSE SAMPLE PAPER DOWNLOADER (2025-26)")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    success = 0
    failed = 0
    
    for filename, url in SAMPLE_PAPERS.items():
        if download_file(url, filename):
            success += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"✅ Downloaded: {success}")
    print(f"❌ Failed: {failed}")
    print("="*60)
    
    if failed > 0:
        print("\n💡 Manual Download Instructions:")
        print("   1. Visit: https://cbseacademic.nic.in/SQP_2024-25.html")
        print("   2. Navigate to 'Class X' → 'Mathematics'")
        print("   3. Download both Standard and Basic papers with Marking Schemes")
        print(f"   4. Save to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
