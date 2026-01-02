import sys
import os
from qdrant_client import models

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings

def list_chapters():
    print("🚀 Scanning Qdrant for Chapters...")
    
    collection_name = settings.QDRANT_COLLECTION_NAME # cbse_textbooks
    
    # We will fetch a large number of points and aggregate distinct chapters
    # Note: In production, you'd use a Facet/Group API, but scroll is fine for <10k items
    
    limit = 2000
    points, _ = qdrant_service.client.scroll(
        collection_name=collection_name,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    structure = {} # {Subject: {Chapter: Count}}
    
    for point in points:
        p = point.payload
        subj = p.get('subject', 'Unknown')
        chap = p.get('chapter', 'Unknown')
        
        if subj not in structure:
            structure[subj] = {}
        
        if chap not in structure[subj]:
            structure[subj][chap] = 0
            
        structure[subj][chap] += 1
        
    print("\n📚 INDEXED CONTENT MAP:")
    for subject, chapters in structure.items():
        print(f"\n📌 SUBJECT: {subject}")
        for chapter, count in chapters.items():
            print(f"   - {chapter}: {count} chunks")

if __name__ == "__main__":
    list_chapters()