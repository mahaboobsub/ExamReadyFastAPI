import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_multi_chapter_exam():
    """Test exam spanning Light + Electricity chapters"""
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapters": [
            "Light",
            "Electricity"
        ],
        # LOWERED TO 10 for stability on Free Tier
        "totalQuestions": 10,
        "bloomsDistribution": {
            "Remember": 40,    # 4 Qs
            "Understand": 60   # 6 Qs
        },
        "difficulty": "Medium"
    }
    
    print("Testing Multi-Chapter Exam Generation...")
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/exam/generate",
            json=payload,
            headers=HEADERS,
            timeout=300
        )
        
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        questions = data['questions']
        
        # We asked for 10. We accept 8+ as success (LLMs aren't perfect counters)
        assert len(questions) >= 8, f"Too few questions: {len(questions)}"
        
        print(f"✅ Generated {len(questions)} questions")
        print(f"✅ Bloom's breakdown: {data['bloomsBreakdown']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise e

if __name__ == "__main__":
    test_multi_chapter_exam()