import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
from app.config.settings import settings

def create_indexes():
    print(f"🔧 Connecting to Qdrant: {settings.QDRANT_URL.split('://')[1].split(':')[0]}...")
    
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=30
    )
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    print(f"🎯 Target Collection: {collection_name}")
    
    # Fields to index for filtering
    # text-dense and text-sparse are already indexed by vector config
    fields = [
        {"name": "board", "type": PayloadSchemaType.KEYWORD},
        {"name": "class", "type": PayloadSchemaType.INTEGER},
        {"name": "subject", "type": PayloadSchemaType.KEYWORD},
        {"name": "chapter", "type": PayloadSchemaType.KEYWORD},
        {"name": "textbook", "type": PayloadSchemaType.KEYWORD}
    ]
    
    print("\n🚀 Creating Payload Indexes...")
    
    for field in fields:
        try:
            print(f"   Indexing '{field['name']}' ({field['type']})...")
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field["name"],
                field_schema=field["type"]
            )
            print(f"   ✅ Success: '{field['name']}' indexed.")
        except Exception as e:
            if "already exists" in str(e) or "already indexed" in str(e):
                print(f"   ℹ️  Skipping: '{field['name']}' (Already exists)")
            else:
                print(f"   ❌ Failed to index '{field['name']}': {e}")
                
    print("\n✨ Indexing setup complete. Filtering should now work.")

if __name__ == "__main__":
    create_indexes()