"""
Reindex All Textbooks with OCR Enhancement
Processes all 14 chapters using pix2text + Tesseract + VLM
"""
import asyncio
import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indexingservice import IndexingService
from app.services.qdrant_service import qdrant_service
from app.config.settings import settings


TEXTBOOK_DIR = "data/textbooks/class_10/mathematics"

TEXTBOOK_FILES = [
    ("jemh101.pdf", 1, "Real Numbers"),
    ("jemh102.pdf", 2, "Polynomials"),
    ("jemh103.pdf", 3, "Pair of Linear Equations in Two Variables"),
    ("jemh104.pdf", 4, "Quadratic Equations"),
    ("jemh105.pdf", 5, "Arithmetic Progressions"),
    ("jemh106.pdf", 6, "Triangles"),
    ("jemh107.pdf", 7, "Coordinate Geometry"),
    ("jemh108.pdf", 8, "Introduction to Trigonometry"),
    ("jemh109.pdf", 9, "Some Applications of Trigonometry"),
    ("jemh110.pdf", 10, "Circles"),
    ("jemh111.pdf", 11, "Areas Related to Circles"),
    ("jemh112.pdf", 12, "Surface Areas and Volumes"),
    ("jemh113.pdf", 13, "Statistics"),
    ("jemh114.pdf", 14, "Probability"),
]


async def process_all():
    print("="*70)
    print("📚 REINDEX ALL TEXTBOOKS WITH OCR ENHANCEMENT")
    print("   Using: PyMuPDF + pix2text + Tesseract + Gemini Vision")
    print("="*70)
    
    # Check textbook directory
    if not os.path.exists(TEXTBOOK_DIR):
        print(f"\n❌ Textbook directory not found: {TEXTBOOK_DIR}")
        return
    
    # Initialize services
    print("\n⚙️ Initializing services...")
    await qdrant_service.initialize()
    indexing_service = IndexingService()
    
    total_chunks = 0
    processed = 0
    failed = 0
    
    for filename, chapter_id, chapter_name in TEXTBOOK_FILES:
        pdf_path = os.path.join(TEXTBOOK_DIR, filename)
        
        if not os.path.exists(pdf_path):
            print(f"\n⚠️ Skipping {filename} (not found)")
            continue
        
        print(f"\n{'='*60}")
        print(f"📖 Chapter {chapter_id}: {chapter_name}")
        print(f"   File: {filename}")
        print(f"{'='*60}")
        
        try:
            # Build metadata
            metadata = {
                "board": "CBSE",
                "class": 10,
                "class_num": 10,
                "subject": "Mathematics",
                "chapter": chapter_name,
                "chapter_id": chapter_id,
                "textbook": "NCERT Mathematics Class 10",
                "processed_with_ocr": True
            }
            
            # Process PDF with OCR pipeline
            chunks = indexing_service.process_pdf(pdf_path, metadata)
            
            if not chunks:
                print(f"   ⚠️ No chunks generated")
                continue
            
            print(f"   📦 Generated {len(chunks)} chunks with embeddings")
            
            # Prepare for Qdrant
            points = []
            embeddings = []
            
            for chunk in chunks:
                chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk['id']))
                points.append({
                    "id": chunk_id,
                    "text": chunk['text'],
                    "metadata": chunk['metadata']
                })
                embeddings.append(chunk['embedding'])
            
            # Upload to Qdrant
            print(f"   ☁️ Uploading to Qdrant...")
            await qdrant_service.upsert_chunks(
                chunks=points,
                embeddings=embeddings,
                collection_name=settings.QDRANT_COLLECTION_NAME
            )
            
            print(f"   ✅ Uploaded {len(points)} chunks")
            total_chunks += len(points)
            processed += 1
            
            # Delay to avoid rate limits
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("🎉 REINDEXING COMPLETE")
    print("="*70)
    print(f"   ✅ Processed: {processed}/{len(TEXTBOOK_FILES)} chapters")
    print(f"   ❌ Failed: {failed}")
    print(f"   📦 Total chunks: {total_chunks}")
    print("="*70)
    
    # Verify collection
    info = await qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
    print(f"\n📊 Collection Status:")
    print(f"   Collection: {settings.QDRANT_COLLECTION_NAME}")
    print(f"   Points: {info.points_count}")
    print(f"   Status: {info.status}")
    
    await qdrant_service.close()


if __name__ == "__main__":
    asyncio.run(process_all())
