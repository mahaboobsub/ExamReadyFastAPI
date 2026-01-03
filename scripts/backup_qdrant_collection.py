"""
Backup Qdrant Collection - Save all points to JSON before cleanup
"""
import json
import asyncio
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings


async def backup():
    print("="*60)
    print("📦 QDRANT COLLECTION BACKUP")
    print("="*60)
    
    await qdrant_service.initialize()
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    print(f"\n📁 Backing up: {collection_name}")
    
    points = []
    offset = None
    batch_num = 0
    
    while True:
        batch_num += 1
        print(f"   Fetching batch {batch_num}...", end=" ")
        
        result = await qdrant_service.client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        batch_points = result[0]
        points.extend(batch_points)
        print(f"got {len(batch_points)} points")
        
        offset = result[1]
        if offset is None:
            break
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_textbooks_{timestamp}.json"
    
    backup_data = []
    for p in points:
        backup_data.append({
            "id": str(p.id),
            "payload": p.payload
        })
    
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Backed up {len(points)} points")
    print(f"📄 Saved to: {backup_file}")
    
    await qdrant_service.close()
    return backup_file


if __name__ == "__main__":
    asyncio.run(backup())
