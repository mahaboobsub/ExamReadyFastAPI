import sys
import os
from qdrant_client import models

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qdrant_service import qdrant_service
from app.config.settings import settings

def check_collection_stats(collection_name: str, subjects: list):
    print(f"\n🔎 Inspecting Collection: '{collection_name}'")
    
    try:
        # 1. Check if collection exists
        if not qdrant_service.client.collection_exists(collection_name):
            print(f"   ❌ Collection '{collection_name}' does not exist!")
            return

        # 2. Get Total Count
        count = qdrant_service.client.count(collection_name).count
        print(f"   📊 Total Vectors: {count}")
        
        if count == 0:
            print("   ⚠️  Collection is empty.")
            return

        # 3. Check per Subject
        print("   Counts by Subject:")
        for subject in subjects:
            filter_condition = models.Filter(
                must=[models.FieldCondition(
                    key="subject",
                    match=models.MatchValue(value=subject)
                )]
            )
            
            subject_count = qdrant_service.client.count(
                collection_name=collection_name,
                count_filter=filter_condition
            ).count
            
            status = "✅" if subject_count > 0 else "❌"
            print(f"     {status} {subject.ljust(15)}: {subject_count}")

    except Exception as e:
        print(f"   ❌ Error checking collection: {e}")

def main():
    print("🚀 Qdrant Data Audit")
    print(f"Endpoint: {settings.QDRANT_URL}")
    
    subjects_to_check = ["Chemistry", "Maths", "Physics", "Biology"]
    
    # Check 1: Raw Textbooks (Context)
    check_collection_stats(settings.QDRANT_COLLECTION_NAME, subjects_to_check)
    
    # Check 2: Question Bank (For Exams)
    check_collection_stats(settings.QDRANT_COLLECTION_QUESTIONS, subjects_to_check)

if __name__ == "__main__":
    main()