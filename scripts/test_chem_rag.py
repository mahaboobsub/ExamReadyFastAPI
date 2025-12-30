import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.qdrant_service import qdrant_service

def test():
    # 1. Semantic Test
    print("🧪 Test 1: Semantic (Concept)")
    res = qdrant_service.hybrid_search(
        "What happens when magnesium burns in air?", 
        {"subject": "Chemistry"}
    )
    print(f"Found {len(res['chunks'])} chunks. Top source: {res['chunks'][0]['metadata']['page']}")

    # 2. Keyword Test
    print("\n🧪 Test 2: Keyword (Specific Reaction)")
    res = qdrant_service.hybrid_search(
        "balance the equation Fe + H2O", 
        {"subject": "Chemistry"}
    )
    print(f"Found {len(res['chunks'])} chunks. Text snippet: {res['chunks'][0]['text'][:50]}...")
    
    # 3. Negative Test (Phase 9)
    print("\n🧪 Test 3: Negative Test (Out of Syllabus)")
    res = qdrant_service.hybrid_search(
        "Describe the structure of an atom and electrons", 
        {"subject": "Chemistry"}
    )
    # Rerank scores should be low
    print(f"Top Score for atomic structure: {res['chunks'][0]['rerank_score']}")

if __name__ == "__main__":
    test()