import json
import glob
from pathlib import Path

def extract_question_fingerprints(exam_path):
    if not Path(exam_path).exists():
        print(f"⚠️ {exam_path} not found.")
        return []
        
    try:
        with open(exam_path, "r", encoding="utf-8") as f:
            exam = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {exam_path}: {e}")
        return []
    
    fingerprints = []
    for section_code, section in exam.get('sections', {}).items():
        for q in section.get('questions', []):
            # Use first 50 chars as fingerprint (lowercase, stripped)
            text = q.get('text', "")
            fp = text[:50].lower().strip()
            fingerprints.append(fp)
    return fingerprints

def compare_exams():
    print("==================================================")
    print("CROSS-EXAM UNIQUENESS CHECK")
    print("==================================================")
    
    exam_files = [
        "test_output/exam_test_005.json",
        "test_output/exam_test_006.json",
        "test_output/exam_test_007.json",
        "test_output/exam_test_008.json"
    ]
    
    all_fingerprints = []
    exam_fps = {}
    
    for f in exam_files:
        fps = extract_question_fingerprints(f)
        if fps:
            print(f"Loaded {f}: {len(fps)} questions")
            exam_fps[f] = set(fps) # Use set for per-exam uniqueness check
            all_fingerprints.extend(fps)
    
    if not all_fingerprints:
        print("No exams loaded.")
        return

    # Global Uniqueness
    total_q = len(all_fingerprints)
    unique_q = len(set(all_fingerprints))
    
    uniqueness_pct = (unique_q / total_q) * 100 if total_q > 0 else 0
    
    print("-" * 50)
    print(f"Total Questions Across Exams: {total_q}")
    print(f"Unique Questions (Fingerprint): {unique_q}")
    print(f"Uniqueness Score: {uniqueness_pct:.2f}%")
    print("-" * 50)
    
    if uniqueness_pct >= 80:
        print("✅ PASSED: Uniqueness > 80%")
    else:
        print("❌ FAILED: Uniqueness < 80%")
        
    # check intersection
    print("\nPairwise Overlap:")
    keys = list(exam_fps.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            f1 = keys[i]
            f2 = keys[j]
            overlap = exam_fps[f1].intersection(exam_fps[f2])
            if overlap:
                print(f"  {f1} vs {f2}: {len(overlap)} overlaps")
                for fp in list(overlap)[:3]:
                    print(f"    - {fp}...")
            else:
                print(f"  {f1} vs {f2}: 0 overlaps ✅")

if __name__ == "__main__":
    compare_exams()
