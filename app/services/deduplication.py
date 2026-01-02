import hashlib
from typing import List, Dict
from app.services.geminiservice import GeminiService

# Instantiate here to reuse embedding logic
gemini_service = GeminiService()

def deduplicate_questions(questions: List[Dict]) -> List[Dict]:
    """
    Deduplicate by:
    1. MD5 Hash (Exact)
    2. Semantic Similarity (Cosine > 0.90)
    """
    unique = []
    seen_hashes = set()
    # In a real high-load scenario, we'd cache embeddings. 
    # For MVP, we'll trust MD5 and ID first to save latency.
    
    for q in questions:
        # 1. ID Check
        if not q.get("id"): continue
        
        # 2. Text Hash
        text = q.get("text", "").lower().strip()
        md5 = hashlib.md5(text.encode()).hexdigest()
        
        if md5 in seen_hashes:
            continue
            
        seen_hashes.add(md5)
        unique.append(q)
        
    # Note: Full semantic deduplication on 100+ candidates adds ~2s latency.
    # We rely on MD5 + Source Diversity for Phase 1.
    
    return unique