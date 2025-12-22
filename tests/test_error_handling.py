import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_auth_failure():
    """Test Invalid X-Internal-Key"""
    print("\n🧪 Testing Auth Failure...")
    resp = requests.post(
        f"{BASE_URL}/v1/exam/generate",
        json={"board": "CBSE"},
        headers={"X-Internal-Key": "WRONG_KEY"}
    )
    if resp.status_code == 403:
        print("   ✅ 403 Forbidden received (Correct)")
    else:
        print(f"   ❌ Failed: Expected 403, got {resp.status_code}")
        raise AssertionError("Auth check failed")

def test_schema_validation():
    """Test Missing Required Fields"""
    print("\n🧪 Testing Schema Validation...")
    # Missing 'class', 'subject', 'chapters'
    resp = requests.post(
        f"{BASE_URL}/v1/exam/generate",
        json={"board": "CBSE"}, 
        headers=HEADERS
    )
    if resp.status_code == 422:
        print("   ✅ 422 Unprocessable Entity received (Correct)")
    else:
        print(f"   ❌ Failed: Expected 422, got {resp.status_code}")
        raise AssertionError("Schema validation failed")

def test_invalid_chapter():
    """Test Non-existent chapter"""
    print("\n🧪 Testing Invalid Chapter...")
    payload = {
        "board": "CBSE", "class": 10, "subject": "Physics",
        "chapters": ["Quantum Physics Advanced"], # Doesn't exist in 10th
        "totalQuestions": 5,
        "bloomsDistribution": {"Remember": 100},
        "difficulty": "Medium"
    }
    resp = requests.post(
        f"{BASE_URL}/v1/exam/generate",
        json=payload,
        headers=HEADERS
    )
    # Should return 200 with empty list OR generic questions, but NOT crash
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Handled gracefully. Questions generated: {len(data['questions'])}")
    else:
        print(f"   ⚠️ API Error: {resp.status_code} (Check logs)")

if __name__ == "__main__":
    test_auth_failure()
    test_schema_validation()
    test_invalid_chapter()