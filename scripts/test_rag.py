import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ragservice import HybridRAGService

def test_rag():
    print("🚀 Initializing RAG Service...")
    rag = HybridRAGService()
    
    # Test Query: Specific Physics Question
    query = "What is the formula for refractive index?"
    
    # Strict Filtering: Only look in CBSE Class 10 Physics
    filters = {"board": "CBSE", "class": 10, "subject": "Physics"}
    
    print(f"\n🔎 Searching for: '{query}'")
    result = rag.search(query, filters)
    
    print(f"\n✅ Search completed in {result['latency']}s")
    print(f"✅ Found {len(result['chunks'])} relevant chunks")
    
    print("\n--- Top Result (Traceability Check) ---")
    if result['chunks']:
        top_chunk = result['chunks'][0]
        # Check if we retrieved the correct page
        print(f"Source Chapter: {top_chunk['metadata'].get('chapter')}")
        print(f"Source Page:    {top_chunk['metadata'].get('page')}")
        print(f"Relevance Score: {top_chunk.get('rerank_score', 0):.4f}")
        print(f"Text Snippet:   {top_chunk['text'][:200]}...")
    else:
        print("❌ No results found. Index might be empty.")

if __name__ == "__main__":
    test_rag()