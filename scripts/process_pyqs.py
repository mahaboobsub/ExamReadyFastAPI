"""
Batch Process PYQ PDFs with Hindi Removal and Solution Detection
Uses the new pdf_processor module
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


PYQ_DIR = "data/pyq/class_10/mathematics"
COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME  # Use textbooks collection


async def main():
    print("="*70)
    print("📚 PYQ BATCH PROCESSOR")
    print("   Features: Hindi Removal + Solution Detection + OCR")
    print("="*70)
    
    # Check PYQ directory
    if not os.path.exists(PYQ_DIR):
        print(f"\n❌ PYQ directory not found: {PYQ_DIR}")
        print("   Please download PYQs first!")
        return
    
    # Find all PDFs
    pdf_files = sorted(glob.glob(os.path.join(PYQ_DIR, "*.pdf")))
    
    if not pdf_files:
        print(f"\n⚠️ No PDF files found in {PYQ_DIR}")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDFs:")
    for f in pdf_files:
        print(f"   • {os.path.basename(f)}")
    
    # Initialize services
    print("\n⚙️ Initializing services...")
    await qdrant_service.initialize()
    gemini_service = GeminiService()
    
    # Create processor
    pyq_processor = PYQProcessor(qdrant_service, gemini_service)
    
    # Process all PYQs
    stats = await pyq_processor.process_multiple_pyqs(
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
