"""
Quick test using app settings (which loads .env automatically)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from qdrant_client import QdrantClient

print("="*70)
print("TESTING QDRANT CONNECTION")
print("="*70)
print(f"QDRANT_URL: {settings.QDRANT_URL}")
print(f"Collection: {settings.QDRANT_COLLECTION_NAME}")
print("="*70)

try:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    # List collections
    collections = client.get_collections()
    print(f"\n✅ Connected to Qdrant!")
    print(f"Found {len(collections.collections)} collections:\n")
    
    for col in collections.collections:
        info = client.get_collection(col.name)
        print(f"  • {col.name}")
        print(f"    Points: {info.points_count}")
        print(f"    Status: {info.status}")
        print()
    
    print("="*70)
    print("READY TO PROCEED WITH SETUP")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Connection failed: {str(e)}")
    print("\nPlease check:")
    print("  1. Qdrant cluster is running")
    print("  2. QDRANT_URL and QDRANT_API_KEY in .env are correct")
