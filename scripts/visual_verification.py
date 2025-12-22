import requests
import json
import time
import os

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def print_json(data, label):
    """Pretty print JSON for inspection"""
    print(f"\n{'='*20} {label} {'='*20}")
    print(json.dumps(data, indent=2))
    print("="*60 + "\n")

def test_basic_exam():
    print("🧪 1. Testing Basic Exam (Light)...")
    payload = {
        "board": "CBSE", "class": 10, "subject": "Physics",
        "chapters": ["Light"],
        "totalQuestions": 3,
        "bloomsDistribution": {"Remember": 100},
        "difficulty": "Medium"
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/exam/generate", json=payload, headers=HEADERS, timeout=120)
        print_json(resp.json(), "BASIC EXAM RESPONSE")
    except Exception as e:
        print(f"❌ Failed: {e}")

def test_multi_chapter():
    print("🧪 2. Testing Multi-Chapter (Light + Electricity)...")
    payload = {
        "board": "CBSE", "class": 10, "subject": "Physics",
        "chapters": ["Light", "Electricity"],
        "totalQuestions": 4, 
        "bloomsDistribution": {"Understand": 50, "Apply": 50},
        "difficulty": "Hard"
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/exam/generate", json=payload, headers=HEADERS, timeout=180)
        print_json(resp.json(), "MULTI-CHAPTER EXAM")
    except Exception as e:
        print(f"❌ Failed: {e}")

def test_quiz():
    print("🧪 3. Testing Quiz (Explanations)...")
    payload = {
        "board": "CBSE", "class": 10, "subject": "Physics",
        "chapters": ["Electricity"],
        "numQuestions": 5, # Corrected to meet validator requirements (ge=5)
        "difficulty": "Medium"
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/quiz/generate", json=payload, headers=HEADERS, timeout=120)
        print_json(resp.json(), "QUIZ RESPONSE (CHECK EXPLANATIONS)")
    except Exception as e:
        print(f"❌ Failed: {e}")

def test_flashcards():
    print("🧪 4. Testing Flashcards...")
    payload = {
        "board": "CBSE", "class": 10, "subject": "Physics",
        "chapter": "Light",
        "cardCount": 5
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/flashcards/generate", json=payload, headers=HEADERS, timeout=120)
        print_json(resp.json(), "FLASHCARDS")
    except Exception as e:
        print(f"❌ Failed: {e}")

def test_tutor():
    print("🧪 5. Testing AI Tutor (Student Mode)...")
    payload = {
        "query": "Why does a pencil look bent in water?",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Light"},
        "mode": "student"
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/tutor/answer", json=payload, headers=HEADERS, timeout=60)
        print_json(resp.json(), "TUTOR ANSWER")
    except Exception as e:
        print(f"❌ Failed: {e}")

def run_visual_audit():
    print("🚀 STARTING VISUAL AUDIT (Raw JSON Inspection)\n")
    
    test_basic_exam()
    time.sleep(5)
    
    test_quiz()
    time.sleep(5)
    
    test_flashcards()
    time.sleep(5)
    
    test_tutor()
    time.sleep(5)
    
    test_multi_chapter()
    
    print("\n🏁 AUDIT COMPLETE")

if __name__ == "__main__":
    run_visual_audit()