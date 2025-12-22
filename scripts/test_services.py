import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.geminiservice import GeminiService
from app.services.chromaservice import ChromaService
from app.services.bm25service import BM25Service

def test_infrastructure():
    print("1️⃣  Testing Gemini Embeddings...")
    gemini = GeminiService()
    vector = gemini.embed("Photosynthesis is a process in plants.")
    if len(vector) == 768:
        print("   ✅ Embedding generated (768 dims)")
    else:
        print("   ❌ Embedding failed")

    print("\n2️⃣  Testing ChromaDB...")
    chroma = ChromaService()
    collection = chroma.create_collection("test_collection")
    # Add dummy data
    chroma.add_documents(collection, [{
        "id": "test_1",
        "text": "This is a test document",
        "embedding": vector,
        "metadata": {"source": "test"}
    }])
    count = collection.count()
    print(f"   ✅ Chroma collection has {count} documents")

    print("\n3️⃣  Testing BM25...")
    bm25 = BM25Service()
    dummy_chunks = [
        {"id": "1", "text": "Newton's laws of motion"},
        {"id": "2", "text": "Einstein's theory of relativity"}
    ]
    bm25.build_index(dummy_chunks)
    bm25.save_index()
    if os.path.exists("data/bm25/index.pkl"):
        print("   ✅ BM25 index saved to disk")

if __name__ == "__main__":
    test_infrastructure()