import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_blooms_distribution():
    """Test mixed distribution request"""
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapters": ["Light"],
        "totalQuestions": 6,
        "bloomsDistribution": {
            "Remember": 50,    # 3 questions
            "Apply": 50        # 3 questions
        },
        "difficulty": "Medium"
    }
    
    print("Testing Bloom's Distribution...")
    resp = requests.post(f"{BASE_URL}/v1/exam/generate", json=payload, headers=HEADERS, timeout=90)
    
    assert resp.status_code == 200
    data = resp.json()
    breakdown = data['bloomsBreakdown']
    
    print(f"   Requested: Remember=3, Apply=3")
    print(f"   Got: {breakdown}")
    
    # Check if we got at least some of each
    assert breakdown.get('Remember', 0) > 0
    assert breakdown.get('Apply', 0) > 0
    print("✅ Distribution logic working")

if __name__ == "__main__":
    test_blooms_distribution()