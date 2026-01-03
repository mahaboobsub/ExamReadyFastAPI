"""
Process NCERT Class 10 Mathematics Textbook into Qdrant RAG
"""
import os
import sys
import asyncio
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyMuPDF for PDF extraction
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf  # Fallback for older installations

from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.settings import settings

# Chapter mapping (from NCERT Class 10 Mathematics)
CHAPTER_MAP = {
    "jemh101.pdf": "Real Numbers",
    "jemh102.pdf": "Polynomials",
    "jemh103.pdf": "Pair of Linear Equations in Two Variables",
    "jemh104.pdf": "Quadratic Equations",
    "jemh105.pdf": "Arithmetic Progressions",
    "jemh106.pdf": "Triangles",
    "jemh107.pdf": "Coordinate Geometry",
    "jemh108.pdf": "Introduction to Trigonometry",
    "jemh109.pdf": "Some Applications of Trigonometry",
    "jemh110.pdf": "Circles",
    "jemh111.pdf": "Areas Related to Circles",
    "jemh112.pdf": "Surface Areas and Volumes",
    "jemh113.pdf": "Statistics",
    "jemh114.pdf": "Probability",
}

TEXTBOOK_DIR = "data/textbooks/class_10/mathematics"
CHUNK_SIZE = 1000  # Characters per chunk
OVERLAP = 200      # Overlap between chunks

gemini = GeminiService()


def extract_text_from_pdf(pdf_path: str) -> list:
    """Extract text page by page from PDF"""
    doc = pymupdf.open(pdf_path)
    pages = []
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():  # Only add non-empty pages
            pages.append({
                "page_num": page_num,
                "text": text
            })
    
    doc.close()
    return pages


def chunk_text(text: str, page_num: int, chunk_size: int, overlap: int) -> list:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append({
                "text": chunk,
                "page": page_num,
                "char_start": start,
                "char_end": end
            })
        
        start += (chunk_size - overlap)
    
    return chunks


async def process_chapter(pdf_filename: str):
    """Process one chapter"""
    chapter_name = CHAPTER_MAP.get(pdf_filename, "Unknown")
    pdf_path = os.path.join(TEXTBOOK_DIR, pdf_filename)
    
    if not os.path.exists(pdf_path):
        print(f"   ⚠️ File not found: {pdf_path}")
        return 0
    
    print(f"\n📖 Processing: {chapter_name}")
    print(f"   File: {pdf_filename}")
    
    # Extract text
    print(f"   📄 Extracting text...")
    pages = extract_text_from_pdf(pdf_path)
    print(f"   ✅ Extracted {len(pages)} pages")
    
    # Create chunks
    all_chunks = []
    for page_data in pages:
        page_chunks = chunk_text(
            page_data["text"], 
            page_data["page_num"], 
            CHUNK_SIZE, 
            OVERLAP
        )
        all_chunks.extend(page_chunks)
    
    print(f"   ✂️ Created {len(all_chunks)} chunks")
    
    if len(all_chunks) == 0:
        print(f"   ⚠️ No text extracted from PDF")
        return 0
    
    # Prepare for Qdrant
    points = []
    texts = []
    
    for idx, chunk in enumerate(all_chunks):
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"maths_10_{pdf_filename}_{chunk['page']}_{idx}"))
        
        metadata = {
            "text": chunk["text"],
            "board": "CBSE",
            "class": 10,
            "class_num": 10,
            "subject": "Mathematics",
            "chapter": chapter_name,
            "page": chunk["page"],
            "textbook": "NCERT Mathematics Class 10",
            "chunk_index": idx,
            "total_chunks": len(all_chunks)
        }
        
        points.append({
            "id": chunk_id,
            "text": chunk["text"],
            "metadata": metadata
        })
        
        texts.append(chunk["text"])
    
    # Generate embeddings
    print(f"   🔢 Generating embeddings...")
    embeddings = gemini.embed_batch(texts)
    
    # Upload to Qdrant
    print(f"   ☁️ Uploading to Qdrant...")
    await qdrant_service.upsert_chunks(
        chunks=points,
        embeddings=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME
    )
    
    print(f"   ✅ Successfully uploaded {len(points)} chunks")
    return len(points)


async def main():
    print("="*60)
    print("📚 MATHEMATICS TEXTBOOK PROCESSING PIPELINE")
    print("="*60)
    
    # Check if textbook directory exists
    if not os.path.exists(TEXTBOOK_DIR):
        print(f"\n❌ Textbook directory not found: {TEXTBOOK_DIR}")
        print("   Please create it and add the NCERT PDFs first.")
        return
    
    # List available PDFs
    available_pdfs = [f for f in os.listdir(TEXTBOOK_DIR) if f.endswith('.pdf')]
    print(f"\n📁 Found {len(available_pdfs)} PDFs in {TEXTBOOK_DIR}")
    
    if len(available_pdfs) == 0:
        print("\n⚠️ No PDF files found!")
        print("   Download NCERT Class 10 Maths chapters from:")
        print("   https://ncert.nic.in/textbook.php?jemh1=0-14")
        return
    
    # Initialize Qdrant
    await qdrant_service.initialize()
    
    # Ensure collection exists
    await qdrant_service.create_collection_if_not_exists()
    
    total_chunks = 0
    processed = 0
    
    # Process each chapter
    for pdf_file in sorted(CHAPTER_MAP.keys()):
        if pdf_file not in available_pdfs:
            print(f"\n⚠️ Skipping {pdf_file} (not found)")
            continue
            
        try:
            chunks = await process_chapter(pdf_file)
            total_chunks += chunks
            processed += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("🎉 PROCESSING COMPLETE")
    print("="*60)
    print(f"✅ Chapters processed: {processed}/{len(available_pdfs)}")
    print(f"✅ Total chunks uploaded: {total_chunks}")
    print("="*60)
    
    await qdrant_service.close()


if __name__ == "__main__":
    asyncio.run(main())
