import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_health_check():
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    assert resp.json()['redis'] == "connected"

def test_exam_generation_api():
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapters": ["Light"],
        "totalQuestions": 3,
        "bloomsDistribution": {"Remember": 100},
        "difficulty": "Easy"
    }
    
    # Increase timeout for LLM generation
    resp = requests.post(f"{BASE_URL}/v1/exam/generate", json=payload, headers=HEADERS, timeout=60)
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Validation
    assert len(data['questions']) == 3
    assert data['totalMarks'] == 3
    assert data['questions'][0]['ragConfidence'] > 0.0
    assert 'ragChunkIds' in data['questions'][0]

def test_tutor_api():
    payload = {
        "query": "Define refraction",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics"},
        "mode": "student"
    }
    
    resp = requests.post(f"{BASE_URL}/v1/tutor/answer", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()['sources']) > 0