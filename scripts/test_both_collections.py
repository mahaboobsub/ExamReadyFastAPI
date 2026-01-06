import os
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Check textbook chunks
try:
    textbooks_info = client.get_collection("cbse_textbooks")
    print("📚 TEXTBOOK CHUNKS (for AI Tutor)")
    print(f"   Collection: cbse_textbooks")
    print(f"   Points: {textbooks_info.points_count}")
    print(f"   Status: {textbooks_info.status}")
except Exception as e:
    print(f"📚 TEXTBOOK CHUNKS: NOT FOUND ({str(e)})")

# Check questions
try:
    questions_info = client.get_collection("cbse_questions_v2")
    print("\n❓ CLASSIFIED QUESTIONS (for Exam Rules)")
    print(f"   Collection: cbse_questions_v2")
    print(f"   Points: {questions_info.points_count}")
    print(f"   Status: {questions_info.status}")
    
    # Test query for Assertion-Reason questions
    results = client.scroll(
        collection_name="cbse_questions_v2",
        scroll_filter={
            "must": [
                {"key": "question_type", "match": {"value": "Assertion-Reason"}},
            ]
        },
        limit=5
    )
    
    print(f"\n✅ Found {len(results[0])} Assertion-Reason questions (sample):")
    for idx, point in enumerate(results[0][:3], 1):
        print(f"   {idx}. {point.payload['question_text'][:80]}...")
        print(f"      Chapter: {point.payload['chapter']}")
        print(f"      Section: {point.payload['section']}")
        
except Exception as e:
    print(f"\n❓ CLASSIFIED QUESTIONS: NOT FOUND ({str(e)})")

print("\n" + "="*70)
print("STATUS SUMMARY")
print("="*70)
