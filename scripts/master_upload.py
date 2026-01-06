"""
Master Upload Script for CBSE Class 10 Mathematics PDFs
Processes PDFs from data/raw/cbse_class10_pdfs/maths/ and uploads to Qdrant
"""
import asyncio
import os
import sys
import json
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.services.indexingservice import IndexingService
from app.config.settings import settings


# PDF directory
PDF_DIR = Path("data/raw/cbse_class10_pdfs/maths")

# Expected PDFs with chapter mapping
EXPECTED_PDFS = {
    "real_numbers.pdf": "Real Numbers",
    "polynomials.pdf": "Polynomials",
    "PAIR OF LINEAR EQUATIONS IN TWO VARIABLES.pdf": "Pair of Linear Equations in Two Variables",
    "quadratic_equations.pdf": "Quadratic Equations",
    "SOME APPLICATIONS OF TRIGONOMETRY.pdf": "Some Applications of Trigonometry",
    "triangles.pdf": "Triangles",
    "CO-ORDINATE GEOMETRY.pdf": "Coordinate Geometry",
    "INTRODUCTION TO TRIGONOMETRY.pdf": "Introduction to Trigonometry",
    "SURFACE_AREAS_AND_VOLUMES.pdf": "Surface Areas and Volumes",
    "statistics.pdf": "Statistics",
    "probability.pdf": "Probability",
    "Full Text Book Markings and Synopsis-Class X.pdf": "Mixed Content"
}


async def process_all_pdfs():
    """
    Process all CBSE PDFs and upload to Qdrant
    """
    print("="*70)
    print("📚 MASTER PDF UPLOAD PIPELINE")
    print("="*70)
    print(f"Source Directory: {PDF_DIR}")
    print(f"Target Collection: {settings.QDRANT_COLLECTION_NAME}")
    print("="*70)
    
    # Verify directory exists
    if not PDF_DIR.exists():
        print(f"❌ PDF directory not found: {PDF_DIR}")
        print(f"\nExpected location: {PDF_DIR.absolute()}")
        return
    
    # Get all PDFs
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    
    if len(pdf_files) == 0:
        print(f"❌ No PDF files found in: {PDF_DIR}")
        return
    
    print(f"\n✅ Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        chapter = EXPECTED_PDFS.get(pdf.name, "Unknown Chapter")
        print(f"   • {pdf.name:<50} ({size_mb:>6.2f} MB) → {chapter}")
    
    if len(pdf_files) != len(EXPECTED_PDFS):
        print(f"\n⚠️ WARNING: Expected {len(EXPECTED_PDFS)} PDFs, found {len(pdf_files)}")
        missing = set(EXPECTED_PDFS.keys()) - {p.name for p in pdf_files}
        if missing:
            print(f"Missing: {', '.join(missing)}")
    
    # Initialize services
    print(f"\n{'='*70}")
    print("⚙️ INITIALIZING SERVICES")
    print("="*70)
    
    await qdrant_service.initialize()
    indexing_service = IndexingService()
    
    print("✅ Qdrant connection established")
    print(f"✅ Collection: {settings.QDRANT_COLLECTION_NAME}")
    
    # Track statistics
    all_chunks = []
    stats = {
        'total_pdfs': len(pdf_files),
        'processed': 0,
        'failed': 0,
        'total_chunks': 0,
        'by_chapter': Counter(),
        'by_pdf': {}
    }
    
    # Process each PDF
    print(f"\n{'='*70}")
    print("📄 PROCESSING PDFs")
    print("="*70)
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        chapter_name = EXPECTED_PDFS.get(pdf_path.name, "Unknown")
        
        print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}")
        print(f"Chapter: {chapter_name}")
        print("-"*70)
        
        try:
            # Process PDF using existing IndexingService
            # This will use PyMuPDF + OCR + VLM
            chunks = await indexing_service.process_textbook_pdf(
                pdf_path=str(pdf_path),
                chapter_name=chapter_name,
                chapter_number=idx,
                board="CBSE",
                class_num=10,
                subject="Mathematics"
            )
            
            chunk_count = len(chunks)
            all_chunks.extend(chunks)
            
            stats['processed'] += 1
            stats['total_chunks'] += chunk_count
            stats['by_chapter'][chapter_name] += chunk_count
            stats['by_pdf'][pdf_path.name] = chunk_count
            
            print(f"✅ Extracted {chunk_count} chunks")
            
        except Exception as e:
            stats['failed'] += 1
            print(f"❌ Error: {str(e)}")
            continue
    
    # Upload to Qdrant
    if stats['total_chunks'] > 0:
        print(f"\n{'='*70}")
        print("📤 UPLOADING TO QDRANT")
        print("="*70)
        print(f"Total chunks to upload: {stats['total_chunks']}")
        
        try:
            await qdrant_service.upsert_chunks(
                chunks=all_chunks,
                collection_name=settings.QDRANT_COLLECTION_NAME
            )
            
            print(f"\n✅ UPLOAD COMPLETE!")
            print(f"   {stats['total_chunks']} chunks uploaded to Qdrant")
            
        except Exception as e:
            print(f"\n❌ Upload failed: {str(e)}")
            stats['upload_failed'] = True
    
    # Generate report
    generate_report(stats)
    
    await qdrant_service.close()


def generate_report(stats):
    """Generate detailed upload report"""
    print(f"\n{'='*70}")
    print("📊 UPLOAD SUMMARY REPORT")
    print("="*70)
    
    print(f"\nProcessing Summary:")
    print(f"  Total PDFs:        {stats['total_pdfs']}")
    print(f"  Successfully processed: {stats['processed']}")
    print(f"  Failed:            {stats['failed']}")
    print(f"  Total Chunks:      {stats['total_chunks']}")
    
    if stats['total_chunks'] > 0:
        print(f"\n📚 Chunks by Chapter:")
        print("-"*70)
        for chapter, count in sorted(stats['by_chapter'].items()):
            percentage = (count / stats['total_chunks']) * 100
            print(f"  {chapter:<45} {count:>4} ({percentage:>5.1f}%)")
        
        print(f"\n📄 Chunks by PDF:")
        print("-"*70)
        for pdf_name, count in sorted(stats['by_pdf'].items(), key=lambda x: -x[1]):
            percentage = (count / stats['total_chunks']) * 100
            print(f"  {pdf_name:<50} {count:>4} ({percentage:>5.1f}%)")
    
    print(f"\n{'='*70}")
    
    # Save report to file
    report_file = Path("data/processed/master_upload_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            'summary': {
                'total_pdfs': stats['total_pdfs'],
                'processed': stats['processed'],
                'failed': stats['failed'],
                'total_chunks': stats['total_chunks']
            },
            'by_chapter': dict(stats['by_chapter']),
            'by_pdf': stats['by_pdf']
        }, f, indent=2)
    
    print(f"📄 Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(process_all_pdfs())
