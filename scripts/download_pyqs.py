"""
Download CBSE Previous Year Question Papers for Class 10 Mathematics (2019-2024)
"""
import requests
import os

OUTPUT_DIR = "data/pyq/class_10/mathematics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CBSE Previous Year Papers (2019-2024)
# Note: URLs may need to be updated based on cbseacademic.nic.in
PYQ_PAPERS = {
    # 2024
    "CBSE_Class10_Maths_2024_Set1.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2024/Mathematics_Set1.pdf",
    
    "CBSE_Class10_Maths_2024_Set2.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2024/Mathematics_Set2.pdf",
    
    "CBSE_Class10_Maths_2024_MS.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2024/Mathematics_MS.pdf",
    
    # 2023
    "CBSE_Class10_Maths_2023_Set1.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2023/Mathematics_Set1.pdf",
    
    "CBSE_Class10_Maths_2023_Set2.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2023/Mathematics_Set2.pdf",
    
    "CBSE_Class10_Maths_2023_MS.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2023/Mathematics_MS.pdf",
    
    # 2022
    "CBSE_Class10_Maths_2022_Set1.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2022/Mathematics_Set1.pdf",
    
    "CBSE_Class10_Maths_2022_Set2.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2022/Mathematics_Set2.pdf",
    
    "CBSE_Class10_Maths_2022_MS.pdf": 
        "https://cbseacademic.nic.in/web_material/PreviousQP/ClassX_2022/Mathematics_MS.pdf",
}


def download_file(url: str, filename: str):
    """Download with error handling"""
    try:
        print(f"\n📥 Downloading: {filename}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, stream=True, timeout=30, headers=headers)
        
        if response.status_code == 200:
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_kb = os.path.getsize(filepath) / 1024
            print(f"   ✅ Success: {size_kb:.2f} KB")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        return False


def main():
    print("="*60)
    print("📥 CBSE PYQ DOWNLOADER (2019-2024)")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    success = 0
    
    for filename, url in PYQ_PAPERS.items():
        if download_file(url, filename):
            success += 1
    
    print("\n" + "="*60)
    print(f"✅ Downloaded: {success}/{len(PYQ_PAPERS)}")
    print("="*60)
    
    if success < len(PYQ_PAPERS):
        print("\n💡 Manual Download:")
        print("   Visit: https://cbseacademic.nic.in/previousqp.html")
        print("   Or search 'CBSE Class 10 Mathematics Previous Year Papers'")
        print(f"   Save to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
