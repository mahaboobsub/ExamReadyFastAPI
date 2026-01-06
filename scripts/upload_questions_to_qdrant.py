"""
Upload classified questions to Qdrant collection
Creates embeddings and uploads with full metadata
"""
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.services.geminiservice import GeminiService
from app.config.settings import settings
import google.generativeai as genai


INPUT_FILE = Path("data/processed/questions/all_questions_classified.json")
COLLECTION_NAME = "cbse_questions_v2"


async def generate_embedding(text: str):
    """Generate embedding using Gemini"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"   ⚠️ Embedding error: {str(e)[:50]}")
        return None


async def upload_questions():
    """
    Main upload pipeline
    """
    print("="*70)
    print("📤 QUESTION UPLOAD TO QDRANT")
    print("="*70)
    
    # Load classified questions
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        print("   Run classify_questions.py first!")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"✅ Loaded {len(questions)} classified questions\n")
    
    # Initialize Qdrant client
    client = QdrantClient(
        url=os.getenv("QDRANT_URL") or settings.QDRANT_URL,
        api_key=os.getenv("QDRANT_API_KEY") or settings.QDRANT_API_KEY
    )
    
    # Configure Gemini (for embeddings)
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY)
    
    print(f"Target Collection: {COLLECTION_NAME}\n")
    print("📋 Generating embeddings and uploading...")
    print("-"*70)
    
    points = []
    uploaded_count = 0
    failed_count = 0
    stats = Counter()
    
    for idx, q in enumerate(questions, 1):
        # Generate embedding
        embedding = await generate_embedding(q['question_text'])
        
        if embedding is None:
            failed_count += 1
            continue
        
        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                'question_text': q['question_text'],
                'solution': q.get('solution', ''),
                'question_number': q.get('question_number', ''),
                'chapter': q.get('chapter', 'Unknown'),
                'question_type': q.get('question_type', 'SA'),
                'marks': q.get('marks') or 2,
                'difficulty': q.get('difficulty', 'Medium'),
                'blooms_level': q.get('blooms_level', 'Understand'),
                'section': q.get('section', 'C'),
                'keywords': q.get('keywords', []),
                'has_sub_parts': q.get('has_sub_parts', False),
                'source_file': q.get('source_file', ''),
                'page_number': q.get('page_number', 0)
            }
        )
        
        points.append(point)
        stats[q.get('question_type', 'Unknown')] += 1
        
        # Upload in batches of 50
        if len(points) >= 50:
            try:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                uploaded_count += len(points)
                print(f"   ✅ Uploaded {uploaded_count}/{len(questions)} questions")
                points = []
            except Exception as e:
                print(f"   ❌ Batch upload error: {str(e)}")
                failed_count += len(points)
                points = []
        
        # Rate limiting
        await asyncio.sleep(0.2)
    
    # Upload remaining
    if points:
        try:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            uploaded_count += len(points)
        except Exception as e:
            print(f"   ❌ Final batch error: {str(e)}")
            failed_count += len(points)
    
    # Verify collection
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 UPLOAD SUMMARY")
    print("="*70)
    print(f"Total Questions:   {len(questions)}")
    print(f"Uploaded:          {uploaded_count}")
    print(f"Failed:            {failed_count}")
    print(f"\nQdrant Collection: {COLLECTION_NAME}")
    print(f"Points Count:      {collection_info.points_count}")
    
    print(f"\n📚 By Question Type:")
    print("-"*70)
    for qtype, count in sorted(stats.items()):
        percentage = (count / uploaded_count) * 100 if uploaded_count > 0 else 0
        print(f"  {qtype:<20} {count:>4} ({percentage:>5.1f}%)")
    
    print(f"\n{'='*70}")
    print("✅ UPLOAD COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(upload_questions())
