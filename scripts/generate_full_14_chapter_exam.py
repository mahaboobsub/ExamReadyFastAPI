#!/usr/bin/env python3
"""
Generate a complete CBSE Class 10 Math Board Exam with all 14 chapters.
This is the ultimate test of the RAG+LLM system.
"""

import requests
import json
import time
from datetime import datetime

def generate_full_exam():
    """Generate complete 14-chapter board exam"""
    
    print("\n" + "="*80)
    print("🚀 GENERATING FULL 14-CHAPTER CBSE BOARD EXAM")
    print("="*80)
    
    # All 14 CBSE Class 10 Math chapters
    chapters = [
        "Real Numbers",
        "Polynomials",
        "Pair of Linear Equations in Two Variables",
        "Quadratic Equations",
        "Arithmetic Progressions",
        "Triangles",
        "Coordinate Geometry",
        "Introduction to Trigonometry",
        "Applications of Trigonometry",
        "Circles",
        "Areas Related to Circles",
        "Surface Areas and Volumes",
        "Statistics",
        "Probability"
    ]
    
    print(f"\n📚 Chapters to cover: {len(chapters)}")
    for idx, ch in enumerate(chapters, 1):
        print(f"   {idx:2d}. {ch}")
    
    print(f"\n⏱️  Starting generation at: {datetime.now().strftime('%H:%M:%S')}")
    print("   Expected time: 5-15 minutes")
    print("   (Grab a coffee! ☕)")
    
    # API endpoint - Using 8001 port as server is running there
    url = "http://127.0.0.1:8001/v1/exam/generate-board"
    
    # Request payload
    payload = {
        "board": "CBSE",
        "class_num": 10,
        "subject": "Mathematics",
        "chapters": chapters  # All 14 chapters
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Key": "dev_secret_key_12345"
    }
    
    print("\n📡 Sending request to FastAPI server...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=900  # 15 minute timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Generation completed in: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            exam = data.get('exam', {})
            
            # Save to file
            output_file = 'full_14_chapter_exam.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(exam, f, indent=2, ensure_ascii=False)
            
            print("\n" + "="*80)
            print("✅ GENERATION SUCCESSFUL!")
            print("="*80)
            
            # Quick stats
            metadata = exam.get('metadata', {})
            print(f"\n📊 EXAM STATISTICS:")
            print(f"   Total Questions: {metadata.get('totalQuestions', 0)}")
            print(f"   Total Marks: {metadata.get('totalMarks', 0)}")
            print(f"   Duration: {metadata.get('duration', 0)} minutes")
            
            # Chapter distribution
            chapter_counts = {}
            for section in exam.get('sections', {}).values():
                for q in section.get('questions', []):
                    ch = q.get('chapter', 'Unknown')
                    chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
            
            chapters_covered = len([ch for ch in chapter_counts if ch != 'Unknown'])
            
            print(f"\n📚 CHAPTER COVERAGE:")
            print(f"   Chapters Covered: {chapters_covered}/14")
            
            for chapter, count in sorted(chapter_counts.items()):
                status = "✅" if chapter != 'Unknown' else "❌"
                print(f"   {status} {chapter:<45} {count} questions")
            
            print(f"\n✅ Exam saved to: {output_file}")
            
            # Success verdict
            if chapters_covered == 14:
                print("\n" + "="*80)
                print("🎉 PERFECT! ALL 14 CHAPTERS COVERED!")
                print("="*80)
                print("This is a Grade A exam. Proceed to validation.")
            elif chapters_covered >= 12:
                print("\n" + "="*80)
                print("✅ EXCELLENT! 12+ chapters covered")
                print("="*80)
                print("This is very good. Minor gaps acceptable.")
            else:
                print("\n" + "="*80)
                print(f"⚠️ WARNING: Only {chapters_covered} chapters covered")
                print("="*80)
                print("Check board_gen_debug.log for generation issues")
            
            return True
            
        else:
            print("\n❌ GENERATION FAILED!")
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ REQUEST TIMEOUT (>15 minutes)")
        print("   This is abnormal. Check:")
        print("   1. FastAPI server is running")
        print("   2. Gemini API key is valid")
        print("   3. No rate limit errors in server logs")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = generate_full_exam()
    
    if success:
        print("\n🎯 NEXT STEP: Run quality validation")
        print("   python scripts/validate_exam_quality.py full_14_chapter_exam.json")
    else:
        print("\n🔍 TROUBLESHOOTING:")
        print("   1. Check FastAPI server logs")
        print("   2. Check generation debug log: board_gen_debug.log")
        print("   3. Verify Gemini API key in .env file")
