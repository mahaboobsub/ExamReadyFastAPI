import requests
import json
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_simple_exam():
    # Ask for just 4 questions total (Fits in 1 batch, 1 API call)
    # This guarantees we stay under the rate limit
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapters": ["Light"],
        "totalQuestions": 4, 
        "bloomsDistribution": {"Remember": 100},
        "difficulty": "Medium"
    }
    
    print("🚀 Sending simple request...")
    start = time.time()
    
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/exam/generate",
            json=payload,
            headers=HEADERS,
            timeout=180
        )
        print(f"⏱️ Time: {time.time() - start:.2f}s")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success! Generated {len(data['questions'])} questions.")
            print(f"📝 Sample: {data['questions'][0]['text']}")
        else:
            print(f"❌ Failed: {resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_exam()