import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_tutor():
    print("Testing AI Tutor...")
    payload = {
        "query": "Define refraction",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Light"},
        "mode": "student"
    }
    
    resp = requests.post(f"{BASE_URL}/v1/tutor/answer", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    
    data = resp.json()
    print(f"✅ Response: {data['response'][:100]}...")
    print(f"✅ Sources: {len(data['sources'])}")

if __name__ == "__main__":
    test_tutor()