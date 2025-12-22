import pytest
from app.services.ragservice import HybridRAGService

# Golden Dataset: Query -> Expected Page in NCERT Class 10 Physics
GOLDEN_DATASET = [
    {
        "query": "What is the formula for refractive index?",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics"},
        "expected_page": 167,  # Approximate page based on your index
        "tolerance": 2         # Allow +/- 2 pages difference
    },
    {
        "query": "Define Power of a lens and its unit",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics"},
        "expected_page": 184, 
        "tolerance": 2
    },
    {
        "query": "Snell's law of refraction",
        "filters": {"board": "CBSE", "class": 10, "subject": "Physics"},
        "expected_page": 167,
        "tolerance": 2
    }
]

@pytest.mark.asyncio
async def test_rag_retrieval_accuracy():
    rag = HybridRAGService()
    
    hits = 0
    total = len(GOLDEN_DATASET)
    
    print("\n")
    for item in GOLDEN_DATASET:
        result = rag.search(item["query"], item["filters"])
        
        # Check if we got results
        assert len(result['chunks']) > 0, f"No chunks found for '{item['query']}'"
        
        # Get top chunk page
        top_page = int(result['chunks'][0]['metadata'].get('page', 0))
        expected = item['expected_page']
        
        # Check accuracy (within tolerance)
        if abs(top_page - expected) <= item['tolerance']:
            print(f"✅ PASS: '{item['query']}' -> Found p{top_page} (Expected p{expected})")
            hits += 1
        else:
            print(f"❌ FAIL: '{item['query']}' -> Found p{top_page} (Expected p{expected})")
            
    accuracy = hits / total
    print(f"\n📊 RAG Accuracy: {accuracy*100:.1f}%")
    assert accuracy >= 0.6, "RAG Accuracy is too low (<60%)"