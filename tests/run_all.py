# tests/run_all.py
import subprocess
import sys
import os

# FORCE UTF-8 ENVIRONMENT FOR WINDOWS
os.environ["PYTHONIOENCODING"] = "utf-8"

TESTS = [
    ("scripts/test_rag.py", "RAG Retrieval"),
    ("tests/test_multi_chapter.py", "Multi-Chapter Exam"),
    ("tests/test_blooms_distribution.py", "Bloom's Logic"),
    ("tests/test_quiz_api.py", "Quiz API"),
    ("tests/test_tutor_api.py", "Tutor API"),
    ("tests/test_flashcards_api.py", "Flashcards API"),
    ("tests/test_error_handling.py", "Error Handling"),
]

print("="*60)
print("🚀 RUNNING FINAL SYSTEM VERIFICATION (WINDOWS SAFE MODE)")
print("="*60)

failed = 0
for script, name in TESTS:
    print(f"\n▶ Running {name}...")
    print("-" * 20)
    
    try:
        # Run subprocess with explicit UTF-8 encoding
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=180,
            encoding='utf-8',
            errors='replace' # Prevent crashing on weird characters
        )
        
        # Print output regardless of success so you can see what happened
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ PASS: {name}")
        else:
            print(f"❌ FAIL: {name}")
            print("--- Error Output ---")
            print(result.stderr)
            failed += 1
            
    except Exception as e:
        print(f"⚠️ ERROR executing {name}: {e}")
        failed += 1

print("\n" + "="*60)
if failed == 0:
    print("🏆 ALL SYSTEMS GO. READY FOR DEPLOYMENT.")
else:
    print(f"⚠️ {failed} tests failed.")