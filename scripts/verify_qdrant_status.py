"""
Verify Qdrant Cloud collection status
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings

async def main():
    await qdrant_service.initialize()
    
    print("\n" + "="*60)
    print("📊 QDRANT COLLECTION STATUS")
    print("="*60)
    
    # Check textbooks collection
    try:
        if await qdrant_service.client.collection_exists(settings.QDRANT_COLLECTION_NAME):
            info = await qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
            print(f"\n✅ Collection: {settings.QDRANT_COLLECTION_NAME}")
            print(f"   Points: {info.points_count}")
            print(f"   Status: {info.status}")
        else:
            print(f"\n❌ Collection '{settings.QDRANT_COLLECTION_NAME}' not found")
    except Exception as e:
        print(f"\n❌ Error checking textbooks: {e}")
    
    # Check questions collection
    try:
        if await qdrant_service.client.collection_exists(settings.QDRANT_COLLECTION_QUESTIONS):
            info = await qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_QUESTIONS)
            print(f"\n✅ Collection: {settings.QDRANT_COLLECTION_QUESTIONS}")
            print(f"   Points: {info.points_count}")
            print(f"   Status: {info.status}")
        else:
            print(f"\n❌ Collection '{settings.QDRANT_COLLECTION_QUESTIONS}' not found")
    except Exception as e:
        print(f"\n❌ Error checking questions: {e}")
    
    print("\n" + "="*60)
    
    await qdrant_service.close()

if __name__ == "__main__":
    asyncio.run(main())
