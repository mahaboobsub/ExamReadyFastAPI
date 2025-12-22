import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indexingservice import IndexingService
from app.services.chromaservice import ChromaService
from app.services.bm25service import BM25Service

# Define the books we downloaded
BOOKS_TO_INDEX = [
    {
        "path": "data/textbooks/cbse/class_10_physics_light.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Light"}
    },
    {
        "path": "data/textbooks/cbse/class_10_physics_eye.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Human Eye"}
    },
    {
        "path": "data/textbooks/cbse/class_10_physics_electricity.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Electricity"}
    },
    {
        "path": "data/textbooks/cbse/class_10_physics_magnetic.pdf",
        "metadata": {"board": "CBSE", "class": 10, "subject": "Physics", "chapter": "Magnetic Effects"}
    }
]

def main():
    print("🚀 Starting Full Indexing Pipeline...")
    
    indexer = IndexingService()
    chroma = ChromaService()
    bm25 = BM25Service()
    
    # 1. Initialize Collections
    collection = chroma.create_collection("ncert_textbooks")
    
    all_chunks_global = []

    # 2. Process Each Book
    for book in BOOKS_TO_INDEX:
        if not os.path.exists(book['path']):
            print(f"⚠️ File not found: {book['path']}")
            continue
            
        # Run Pipeline: PDF -> Text/Vision -> Chunks -> Embeddings
        chunks = indexer.process_pdf(book['path'], book['metadata'])
        
        # Save to Chroma
        chroma.add_documents(collection, chunks)
        
        # Collect for BM25 (Global Index)
        all_chunks_global.extend(chunks)
        print(f"✅ Finished {book['metadata']['chapter']}")

    # 3. Build & Save BM25 Index (Global)
    if all_chunks_global:
        print("📚 Building Global BM25 Index...")
        bm25.build_index(all_chunks_global)
        bm25.save_index()
        print(f"✨ Indexing Complete! Total Chunks: {len(all_chunks_global)}")
    else:
        print("❌ No chunks were generated.")

if __name__ == "__main__":
    main()