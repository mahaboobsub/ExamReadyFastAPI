import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_quiz_generation():
    """Test quiz generation with explanations"""
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapters": ["Light"],
        "numQuestions": 5,
        "difficulty": "Easy"
    }
    
    print("Testing Quiz API...")
    resp = requests.post(f"{BASE_URL}/v1/quiz/generate", json=payload, headers=HEADERS, timeout=60)
    
    assert resp.status_code == 200, f"Failed: {resp.text}"
    data = resp.json()
    
    q = data['questions'][0]
    assert 'explanation' in q
    assert len(q['explanation']) > 10
    
    print(f"✅ Quiz Generated. Sample Explanation: {q['explanation'][:50]}...")

if __name__ == "__main__":
    test_quiz_generation()