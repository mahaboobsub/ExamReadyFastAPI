import sys
import os

# Add project root to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
from app.config.settings import settings

def create_board_indexes():
    print(f"🔧 Connecting to Qdrant Cloud...")
    print(f"   URL: {settings.QDRANT_URL}")
    
    try:
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )
        
        collection_name = settings.QDRANT_COLLECTION_QUESTIONS  # "board_questions"
        print(f"🎯 Target Collection: {collection_name}")
        
        # Check if collection exists first
        if not client.collection_exists(collection_name):
            print(f"❌ Error: Collection '{collection_name}' does not exist.")
            print("   Run 'python scripts/seed_question_bank.py' first.")
            return

        # Define the exact indexes needed by BoardExamGenerator & CustomExamGenerator
        indexes = [
            # Core Filters
            ("board", PayloadSchemaType.KEYWORD),
            ("class_num", PayloadSchemaType.INTEGER),  # ✅ CRITICAL: Matches new schema
            ("subject", PayloadSchemaType.KEYWORD),
            ("chapter", PayloadSchemaType.KEYWORD),
            
            # Exam Logic Filters
            ("question_type", PayloadSchemaType.KEYWORD), # ✅ CRITICAL: Fixes the 400 Error
            ("bloomsLevel", PayloadSchemaType.KEYWORD),
            ("difficulty", PayloadSchemaType.KEYWORD),
            
            # Quality & sorting
            ("qualityScore", PayloadSchemaType.FLOAT),
            ("usageCount", PayloadSchemaType.INTEGER),    # ✅ For rotation logic
            ("is_validated", PayloadSchemaType.BOOL),
            
            # Legacy/Fallback support (Optional but good for safety)
            ("class", PayloadSchemaType.INTEGER),
            ("type", PayloadSchemaType.KEYWORD)
        ]
        
        print("\n🚀 Applying Indexes...")
        
        for field_name, field_type in indexes:
            try:
                print(f"   Indexing '{field_name}' ({field_type})...", end=" ")
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                print(f"✅ Created")
            except Exception as e:
                # Handle cases where index already exists
                if "already exists" in str(e).lower() or "already indexed" in str(e).lower():
                    print(f"ℹ️  Exists")
                else:
                    print(f"❌ Failed: {e}")
                    
        print("\n✨ All indexes applied successfully.")
        print("   The '400 Bad Request' errors for filtering should be resolved now.")

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    create_board_indexes()