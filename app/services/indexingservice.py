from app.utils.pdfextractor import PDFExtractor
from app.services.visionservice import VisionService
from app.services.geminiservice import GeminiService
from typing import List, Dict, Any

class IndexingService:
    """Orchestrates PDF -> RAG Chunks (Smart Hybrid)"""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.vision_service = VisionService()
        self.gemini_service = GeminiService()

    def process_pdf(self, pdf_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        print(f"📖 Processing: {pdf_path}")
        
        pages = self.pdf_extractor.extract_pdf(pdf_path)
        all_chunks = []

        for page in pages:
            page_text = page['text']
            page_num = page['page_num']
            
            # --- IMAGE PROCESSING ---
            processed_count = 0
            for img in page['images']:
                if processed_count >= 2: break # Limit per page
                
                # 1. Use Local Extraction (if available)
                if img['extracted_text']:
                    print(f"   🔍 Local OCR ({img['type']}) on p{page_num}")
                    page_text += f"\n\n{img['extracted_text']}\n"
                    processed_count += 1
                
                # 2. Use Gemini Vision (ONLY if needed)
                elif img['needs_vision']:
                    print(f"   👁️  Gemini Vision (Pure Diagram) on p{page_num}...")
                    desc = self.vision_service.describe_diagram(img['bytes'])
                    if desc:
                        page_text += f"\n\n[DIAGRAM VISUAL DESCRIPTION]: {desc}\n"
                    processed_count += 1
            # ------------------------

            # Chunking (Standard)
            chunks = self._create_chunks(page_text, chunk_size=1000, overlap=200)
            
            for chunk_text in chunks:
                chunk_id = f"{metadata['subject']}_ch{metadata.get('chapter_id','0')}_p{page_num}_{len(all_chunks)}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {**metadata, "page": page_num, "source": pdf_path}
                })
        
        # Embeddings
        if all_chunks:
            print(f"🧠 Generating embeddings for {len(all_chunks)} chunks...")
            texts = [c['text'] for c in all_chunks]
            embeddings = self.gemini_service.embed_batch(texts)
            for i, chunk in enumerate(all_chunks):
                chunk['embedding'] = embeddings[i]

        return all_chunks

    def _create_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        if not text: return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:
                    end = start + break_point + 1
            chunks.append(text[start:end].strip())
            start = end - overlap
        return chunks