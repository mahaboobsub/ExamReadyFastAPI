from qdrant_client import QdrantClient, models
from app.config.settings import settings

client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

def create_indexes():
    print("🚀 Creating indexes for 'cbse_textbooks'...")
    try:
        # Subject
        client.create_payload_index(
            collection_name="cbse_textbooks",
            field_name="subject",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print("   ✅ Indexed 'subject'")
        
        # Chapter
        client.create_payload_index(
            collection_name="cbse_textbooks",
            field_name="chapter",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print("   ✅ Indexed 'chapter'")

        # Content Type (question, solution, textbook_chapter)
        client.create_payload_index(
            collection_name="cbse_textbooks",
            field_name="content_type",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print("   ✅ Indexed 'content_type'")

        # NEW: Board (Keyword)
        client.create_payload_index(
            collection_name="cbse_textbooks",
            field_name="board",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        print("   ✅ Indexed 'board'")

        # NEW: Class (Integer)
        client.create_payload_index(
            collection_name="cbse_textbooks",
            field_name="class",
            field_schema=models.PayloadSchemaType.INTEGER
        )
        print("   ✅ Indexed 'class'")

        print("🎉 Done!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_indexes()
