"""
Batch Process Sample Paper PDFs with Hindi Removal and Solution Detection
"""
import os
import sys
import asyncio
import glob

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pdf_processor import PYQProcessor
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.settings import settings


SAMPLE_DIR = "data/sample_papers/class_10/mathematics"
COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME


async def main():
    print("="*70)
    print("📝 SAMPLE PAPER BATCH PROCESSOR")
    print("   Features: Hindi Removal + Solution Detection + OCR")
    print("="*70)
    
    # Check directory
    if not os.path.exists(SAMPLE_DIR):
        print(f"\n❌ Sample paper directory not found: {SAMPLE_DIR}")
        return
    
    # Find all PDFs
    pdf_files = sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.pdf")))
    
    if not pdf_files:
        print(f"\n⚠️ No PDF files found in {SAMPLE_DIR}")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDFs:")
    for f in pdf_files:
        print(f"   • {os.path.basename(f)}")
    
    # Initialize services
    print("\n⚙️ Initializing services...")
    await qdrant_service.initialize()
    gemini_service = GeminiService()
    
    # Create processor (reusing PYQProcessor - same logic applies)
    processor = PYQProcessor(qdrant_service, gemini_service)
    
    # Process all sample papers
    stats = await processor.process_multiple_pyqs(
        pdf_paths=pdf_files,
        collection_name=COLLECTION_NAME
    )
    
    # Verify
    print("\n🔍 Verifying Qdrant status...")
    info = await qdrant_service.client.get_collection(COLLECTION_NAME)
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Total Points: {info.points_count}")
    
    await qdrant_service.close()


if __name__ == "__main__":
    asyncio.run(main())
