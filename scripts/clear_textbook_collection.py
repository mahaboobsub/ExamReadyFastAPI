"""
Clear Textbook Collection - Delete and recreate for fresh reindexing
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings


async def clear():
    print("="*60)
    print("🗑️ CLEAR TEXTBOOK COLLECTION")
    print("="*60)
    
    await qdrant_service.initialize()
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    
    # Check current status
    try:
        info = await qdrant_service.client.get_collection(collection_name)
        print(f"\n📊 Current collection: {collection_name}")
        print(f"   Points: {info.points_count}")
    except Exception as e:
        print(f"\n⚠️ Collection doesn't exist: {e}")
    
    # Confirm deletion
    print(f"\n⚠️ WARNING: This will DELETE all data in '{collection_name}'")
    confirm = input("   Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("❌ Aborted")
        await qdrant_service.close()
        return
    
    # Delete collection
    print(f"\n🗑️ Deleting collection: {collection_name}")
    try:
        await qdrant_service.client.delete_collection(
            collection_name=collection_name
        )
        print("   ✅ Collection deleted")
    except Exception as e:
        print(f"   ⚠️ Delete error (may not exist): {e}")
    
    # Recreate collection
    print(f"\n📦 Creating fresh collection: {collection_name}")
    await qdrant_service.create_collection_if_not_exists()
    print("   ✅ Fresh collection created")
    
    # Verify
    info = await qdrant_service.client.get_collection(collection_name)
    print(f"\n📊 New collection status:")
    print(f"   Points: {info.points_count}")
    print(f"   Status: {info.status}")
    
    await qdrant_service.close()


if __name__ == "__main__":
    asyncio.run(clear())
