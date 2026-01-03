"""
PYQ (Previous Year Question) Processor
Processes CBSE PYQ PDFs and stores in Qdrant with proper classification
"""
import os
import re
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .pdf_extractor import PDFProcessor
from .solution_detector import is_likely_marking_scheme_file


class PYQProcessor:
    """
    Process CBSE Previous Year Question papers and Marking Schemes
    - Extracts text with OCR
    - Removes Hindi from question papers
    - Preserves Hindi in marking schemes (for reference)
    - Stores in Qdrant with proper metadata
    """
    
    def __init__(self, qdrant_service, gemini_service):
        """
        Initialize PYQ Processor
        
        Args:
            qdrant_service: Initialized QdrantService instance
            gemini_service: Initialized GeminiService instance
        """
        self.qdrant_service = qdrant_service
        self.gemini_service = gemini_service
        self.pdf_processor = PDFProcessor(use_ocr=True, use_vision=False)
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from PYQ filename
        
        Expected formats:
        - CBSE_Class10_Maths_2024_Set1.pdf
        - CBSE_Class10_Maths_Standard_2024_Set1.pdf
        - CBSE_Class10_Maths_2024_MS.pdf (Marking Scheme)
        
        Args:
            filename: PDF filename
            
        Returns:
            Dictionary with extracted metadata
        """
        filename_lower = filename.lower()
        
        # Extract year
        year_match = re.search(r'(20\d{2})', filename)
        year = year_match.group(1) if year_match else str(datetime.now().year)
        
        # Extract class
        class_match = re.search(r'class[_\s]*(\d+)', filename_lower)
        class_num = int(class_match.group(1)) if class_match else 10
        
        # Extract set number
        set_match = re.search(r'set[_\s]*(\d+)', filename_lower)
        set_num = set_match.group(1) if set_match else "1"
        
        # Determine paper type (Standard/Basic)
        if 'standard' in filename_lower:
            paper_type = "Standard"
        elif 'basic' in filename_lower:
            paper_type = "Basic"
        else:
            paper_type = "Standard"  # Default
        
        # Check if marking scheme
        is_marking_scheme = is_likely_marking_scheme_file(filename)
        
        # Extract subject
        subject = "Mathematics"  # Default for this processor
        if 'maths' in filename_lower or 'math' in filename_lower:
            subject = "Mathematics"
        elif 'science' in filename_lower:
            subject = "Science"
        
        return {
            "year": year,
            "class_num": class_num,
            "set_num": set_num,
            "paper_type": paper_type,
            "subject": subject,
            "is_marking_scheme": is_marking_scheme,
            "source": "PYQ",
            "board": "CBSE"
        }
    
    async def process_pyq(
        self,
        pdf_path: str,
        collection_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Process a single PYQ PDF and store in Qdrant
        
        Args:
            pdf_path: Path to PDF file
            collection_name: Qdrant collection to store in
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Processing statistics
        """
        filename = os.path.basename(pdf_path)
        print(f"\n{'='*60}")
        print(f"📄 Processing PYQ: {filename}")
        print(f"{'='*60}")
        
        # Extract metadata from filename
        metadata = self.extract_metadata_from_filename(filename)
        metadata["pdf_path"] = pdf_path
        
        print(f"   Year: {metadata['year']} | Class: {metadata['class_num']} | Set: {metadata['set_num']}")
        print(f"   Type: {'Marking Scheme' if metadata['is_marking_scheme'] else 'Question Paper'}")
        
        # Extract PDF content
        # Don't remove Hindi from marking schemes (preserve solution text)
        remove_hindi = not metadata['is_marking_scheme']
        pages_data = self.pdf_processor.extract_pdf(pdf_path, remove_hindi=remove_hindi)
        
        print(f"   📑 Extracted {len(pages_data)} pages")
        
        # Count content types
        question_pages = sum(1 for p in pages_data if p['content_type'] == 'question')
        solution_pages = sum(1 for p in pages_data if p['content_type'] == 'solution')
        print(f"   ├─ Question pages: {question_pages}")
        print(f"   └─ Solution pages: {solution_pages}")
        
        # Create chunks
        all_chunks = []
        for page_data in pages_data:
            page_chunks = self._create_chunks(
                page_data['text'],
                chunk_size,
                chunk_overlap
            )
            
            for idx, chunk_text in enumerate(page_chunks):
                chunk_id = str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"pyq_{metadata['year']}_{metadata['set_num']}_p{page_data['page_num']}_{idx}"
                ))
                
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        **metadata,
                        "page_num": page_data['page_num'],
                        "content_type": page_data['content_type'],
                        "chunk_index": idx
                    }
                })
        
        print(f"   ✂️ Created {len(all_chunks)} chunks")
        
        if not all_chunks:
            print(f"   ⚠️ No chunks to process!")
            return {"pages": 0, "chunks": 0, "filename": filename}
        
        # Generate embeddings
        print(f"   🔢 Generating embeddings...")
        texts = [c['text'] for c in all_chunks]
        embeddings = self.gemini_service.embed_batch(texts)
        
        # Upload to Qdrant
        print(f"   ☁️ Uploading to Qdrant...")
        await self.qdrant_service.upsert_chunks(
            chunks=all_chunks,
            embeddings=embeddings,
            collection_name=collection_name
        )
        
        print(f"   ✅ Successfully uploaded {len(all_chunks)} chunks")
        
        return {
            "filename": filename,
            "pages": len(pages_data),
            "chunks": len(all_chunks),
            "question_pages": question_pages,
            "solution_pages": solution_pages,
            "metadata": metadata
        }
    
    async def process_multiple_pyqs(
        self,
        pdf_paths: List[str],
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Process multiple PYQ PDFs
        
        Args:
            pdf_paths: List of PDF file paths
            collection_name: Qdrant collection name
            
        Returns:
            Overall processing statistics
        """
        print("="*70)
        print("📚 PYQ BATCH PROCESSING")
        print("="*70)
        print(f"   PDFs to process: {len(pdf_paths)}")
        
        total_stats = {
            "total_files": len(pdf_paths),
            "processed": 0,
            "failed": 0,
            "total_pages": 0,
            "total_chunks": 0,
            "question_pages": 0,
            "solution_pages": 0
        }
        
        for pdf_path in pdf_paths:
            try:
                stats = await self.process_pyq(pdf_path, collection_name)
                
                total_stats["processed"] += 1
                total_stats["total_pages"] += stats["pages"]
                total_stats["total_chunks"] += stats["chunks"]
                total_stats["question_pages"] += stats["question_pages"]
                total_stats["solution_pages"] += stats["solution_pages"]
                
                # Small delay to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing {pdf_path}: {e}")
                total_stats["failed"] += 1
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 PYQ BATCH PROCESSING COMPLETE")
        print("="*70)
        print(f"   ✅ Processed: {total_stats['processed']}/{total_stats['total_files']}")
        print(f"   ❌ Failed: {total_stats['failed']}")
        print(f"   📄 Total pages: {total_stats['total_pages']}")
        print(f"   📦 Total chunks: {total_stats['total_chunks']}")
        print(f"   ❓ Question pages: {total_stats['question_pages']}")
        print(f"   ✓ Solution pages: {total_stats['solution_pages']}")
        print("="*70)
        
        return total_stats
    
    def _create_chunks(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) < 50:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:
                    end = start + break_point + 1
                    chunk = text[start:end]
            
            cleaned_chunk = chunk.strip()
            if cleaned_chunk:
                chunks.append(cleaned_chunk)
            
            start = end - overlap
        
        return chunks
