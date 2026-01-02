import sys
import os
import uuid
import time

# Add project root to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indexingservice import IndexingService
from app.services.qdrant_service import qdrant_service
from app.config.settings import settings

# --- CONFIGURATION: BOOKS TO INDEX ---
# Update this list based on the PDFs you downloaded in Phase 0
BOOKS_TO_INDEX = [
    # # 🧪 CHEMISTRY (Class 10)
    # {
    #     "path": "data/textbooks/cbse/class_10_chemistry_ch1.pdf",
    #     "metadata": {
    #         "board": "CBSE", 
    #         "class": 10, 
    #         "subject": "Chemistry", 
    #         "chapter": "Chemical Reactions and Equations",
    #         "textbook": "NCERT Class 10 Science"
    #     }
    # },
    # {
    #     "path": "data/textbooks/cbse/class_10_chemistry_ch2.pdf",
    #     "metadata": {
    #         "board": "CBSE", 
    #         "class": 10, 
    #         "subject": "Chemistry", 
    #         "chapter": "Acids, Bases and Salts",
    #         "textbook": "NCERT Class 10 Science"
    #     }
    # },
    
    # 🔭 PHYSICS (Class 10 - Uncomment if you have these downloaded)
    # {
    #     "path": "data/textbooks/cbse/class_10_physics_light.pdf",
    #     "metadata": {
    #         "board": "CBSE", 
    #         "class": 10, 
    #         "subject": "Physics", 
    #         "chapter": "Light",
    #         "textbook": "NCERT Class 10 Science"
    #     }
    # },
    # 📐 MATHS (Class 10)
    # 📐 MATHS (Class 10)
    {
        "path": "data/textbooks/cbse/class_10_maths_ch1.pdf",
        "metadata": {
            "board": "CBSE", 
            "class": 10, 
            "subject": "Maths", 
            "chapter": "Real Numbers",
            "textbook": "NCERT Class 10 Maths"
        }
    },
    {
        "path": "data/textbooks/cbse/class_10_maths_ch2.pdf",
        "metadata": {
            "board": "CBSE", 
            "class": 10, 
            "subject": "Maths", 
            "chapter": "Polynomials",
            "textbook": "NCERT Class 10 Maths"
        }
    }
]

def main():
    print(f"🚀 Starting Migration to Qdrant Cloud")
    print(f"🎯 Target Collection: {settings.QDRANT_COLLECTION_NAME}")
    
    # 1. Initialize Services
    indexer = IndexingService()
    
    # 2. Ensure Collection Exists
    try:
        qdrant_service.create_collection_if_not_exists()
    except Exception as e:
        print(f"⚠️ Error checking collection (might already exist): {e}")

    total_books = len(BOOKS_TO_INDEX)
    
    for i, book in enumerate(BOOKS_TO_INDEX):
        pdf_path = book['path']
        metadata = book['metadata']
        
        print(f"\n📘 Processing Book {i+1}/{total_books}: {metadata['chapter']}...")
        
        if not os.path.exists(pdf_path):
            print(f"   ❌ File not found: {pdf_path}")
            print(f"      Run 'python scripts/download_chemistry_units.py' first!")
            continue

        # A. Process PDF (Extract Text -> Vision -> Chunk -> Dense Embeddings)
        # The IndexingService handles Gemini embeddings internally
        try:
            chunks = indexer.process_pdf(pdf_path, metadata)
            
            if not chunks:
                print("   ⚠️ No chunks extracted. Skipping upsert.")
                continue
                
            print(f"   📦 Extracted {len(chunks)} chunks with dense embeddings.")

            # B. Prepare Embeddings List
            # IndexingService attaches 'embedding' to each chunk dict
            embeddings = [c['embedding'] for c in chunks]
            
            # C. Upsert to Qdrant
            # qdrant_service will generate Sparse Vectors (BM25) internally before uploading
            qdrant_service.upsert_chunks(chunks, embeddings)
            
            print(f"   ✅ Successfully indexed: {metadata['chapter']}")
            
        except Exception as e:
            print(f"   ❌ Failed to process {pdf_path}: {e}")
            import traceback
            traceback.print_exc()

    # Final Stats
    try:
        info = qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
        print(f"\n✨ Migration Complete!")
        print(f"📊 Total Vectors in Qdrant: {info.points_count}")
        print(f"🟢 Status: {info.status}")
    except Exception as e:
        print(f"⚠️ Could not fetch final stats: {e}")

if __name__ == "__main__":
    main()