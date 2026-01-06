"""
Setup dedicated Qdrant collection for CBSE questions
This is separate from the textbook chunks collection
"""
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
from app.config.settings import settings


QUESTION_COLLECTION = "cbse_questions_v2"


async def create_question_collection():
    """
    Create dedicated collection for classified CBSE questions
    """
    print("="*70)
    print("🔧 SETTING UP QUESTION COLLECTION")
    print("="*70)
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL") or settings.QDRANT_URL,
        api_key=os.getenv("QDRANT_API_KEY") or settings.QDRANT_API_KEY
    )
    
    # Delete if exists
    try:
        client.delete_collection(collection_name=QUESTION_COLLECTION)
        print(f"✅ Deleted existing collection: {QUESTION_COLLECTION}")
    except Exception as e:
        print(f"ℹ️ Collection doesn't exist yet (first run)")
    
    # Create new collection with Gemini embedding dimensions
    client.create_collection(
        collection_name=QUESTION_COLLECTION,
        vectors_config={
            "default": VectorParams(
                size=768,  # Gemini text-embedding-004 dimension
                distance=Distance.COSINE
            )
        }
    )
    
    print(f"✅ Created collection: {QUESTION_COLLECTION}")
    print(f"   Vector size: 768 (Gemini embeddings)")
    print(f"   Distance: COSINE")
    
    # Create payload indexes for filtering
    indexes_to_create = [
        ("chapter", PayloadSchemaType.KEYWORD),
        ("question_type", PayloadSchemaType.KEYWORD),
        ("difficulty", PayloadSchemaType.KEYWORD),
        ("section", PayloadSchemaType.KEYWORD),
        ("blooms_level", PayloadSchemaType.KEYWORD),
    ]
    
    print(f"\n📋 Creating payload indexes...")
    for field_name, schema_type in indexes_to_create:
        try:
            client.create_payload_index(
                collection_name=QUESTION_COLLECTION,
                field_name=field_name,
                field_schema=schema_type
            )
            print(f"   ✅ {field_name}")
        except Exception as e:
            print(f"   ⚠️ {field_name}: {str(e)}")
    
    # Verify collection
    collection_info = client.get_collection(collection_name=QUESTION_COLLECTION)
    
    print(f"\n{'='*70}")
    print("✅ COLLECTION SETUP COMPLETE")
    print("="*70)
    print(f"Collection Name: {QUESTION_COLLECTION}")
    print(f"Status: {collection_info.status}")
    print(f"Vectors Count: {collection_info.vectors_count}")
    print(f"Points Count: {collection_info.points_count}")
    print("="*70)
    
    return client


if __name__ == "__main__":
    import asyncio
    asyncio.run(create_question_collection())
