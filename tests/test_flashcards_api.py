import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_flashcard_generation():
    """Test flashcard generation with 4 types"""
    print("\n🧪 Testing Flashcard API...")
    payload = {
        "board": "CBSE",
        "class": 10,
        "subject": "Physics",
        "chapter": "Light",
        "cardCount": 10
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/v1/flashcards/generate",
            json=payload,
            headers=HEADERS,
            timeout=60
        )
        
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # 1. Non-empty list
        cards = data.get('flashcards', [])
        assert len(cards) >= 5, f"Too few cards: {len(cards)}"
        
        # 2. Correct card types
        # We define valid types in the prompt, let's see what we got
        valid_types = ['definition', 'formula', 'concept', 'example']
        types_found = set(c['type'] for c in cards)
        
        print(f"   ✅ Generated {len(cards)} cards")
        print(f"   ✅ Types found: {types_found}")
        
        # Check definitions
        has_def = any(c['type'] == 'definition' for c in cards)
        assert has_def, "Missing 'definition' card type"
        
        # Check structure
        sample = cards[0]
        assert 'front' in sample and 'back' in sample, "Malformed card structure"
        print(f"   ✅ Sample: {sample['front']} -> {sample['back'][:50]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise e

if __name__ == "__main__":
    test_flashcard_generation()