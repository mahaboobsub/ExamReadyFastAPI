import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings

async def main():
    print("🚀 Scanning Qdrant for Chapter Names...")
    await qdrant_service.initialize()
    
    # Scroll through textbooks collection
    results, _ = await qdrant_service.client.scroll(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        limit=2000, # Get enough points to see all chapters
        with_payload=True,
        with_vectors=False
    )
    
    mapping = {} # Subject -> Set(Chapters)
    
    for point in results:
        meta = point.payload
        subj = meta.get('subject', 'Unknown')
        chap = meta.get('chapter', 'Unknown')
        
        if subj not in mapping: mapping[subj] = set()
        mapping[subj].add(chap)
        
    print("\n📚 FOUND CHAPTERS:")
    for subj, chapters in mapping.items():
        print(f"\n📌 {subj}:")
        for chap in sorted(chapters):
            print(f"   - {chap}")
            
    await qdrant_service.close()

if __name__ == "__main__":
    asyncio.run(main())