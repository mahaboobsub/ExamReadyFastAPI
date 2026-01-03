#!/usr/bin/env python3
"""
Check which CBSE Class 10 Math chapters have data in Qdrant.
Determines if we can generate full 14-chapter exam or need fallback.
Uses cloud Qdrant from project settings.
"""

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

def check_qdrant_coverage():
    """Check data availability for all 14 CBSE chapters"""
    
    print("\n" + "="*80)
    print("📊 QDRANT DATA COVERAGE CHECK - CBSE Class 10 Mathematics")
    print("="*80)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    if not qdrant_url or not qdrant_api_key:
        print("❌ ERROR: QDRANT_URL or QDRANT_API_KEY not found in .env")
        return
    
    # Initialize Qdrant client (cloud)
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    # All 14 CBSE Class 10 Math chapters
    chapters = [
        "Real Numbers",
        "Polynomials",
        "Pair of Linear Equations in Two Variables",
        "Quadratic Equations",
        "Arithmetic Progressions",
        "Triangles",
        "Coordinate Geometry",
        "Introduction to Trigonometry",
        "Applications of Trigonometry",
        "Circles",
        "Areas Related to Circles",
        "Surface Areas and Volumes",
        "Statistics",
        "Probability"
    ]
    
    collection_name = "cbse_textbooks"
    
    # Check if collection exists
    try:
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            print(f"❌ ERROR: Collection '{collection_name}' not found!")
            print(f"   Available collections: {[c.name for c in collections]}")
            return
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to Qdrant: {e}")
        return
    
    print(f"\n✅ Connected to Qdrant Cloud")
    print(f"   Collection: {collection_name}")
    print(f"   Checking coverage for {len(chapters)} chapters...\n")
    
    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"   Total vectors in collection: {collection_info.points_count}")
    
    # Check each chapter
    results = []
    total_chunks = 0
    chapters_with_data = 0
    
    for idx, chapter in enumerate(chapters, 1):
        try:
            # Search for chunks mentioning this chapter
            response = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="subject",
                            match=MatchValue(value="Mathematics")
                        )
                    ]
                ),
                limit=500,
                with_payload=True,
                with_vectors=False
            )
            
            # Count chunks mentioning this chapter
            count = 0
            for point in response[0]:
                payload = point.payload
                chapter_field = str(payload.get('chapter', '')).lower()
                text_field = str(payload.get('text', '')).lower()
                
                # Flexible matching
                chapter_lower = chapter.lower()
                chapter_keywords = chapter_lower.replace("introduction to ", "").replace("applications of ", "").replace("areas related to ", "").replace("surface areas and ", "").replace("pair of ", "")
                
                if chapter_lower in chapter_field or chapter_keywords in chapter_field or chapter_lower in text_field:
                    count += 1
            
            total_chunks += count
            
            if count >= 5:
                status = "✅ GOOD"
                chapters_with_data += 1
            elif count >= 2:
                status = "⚠️ SPARSE"
                chapters_with_data += 1
            else:
                status = "❌ MISSING"
            
            results.append({
                'chapter': chapter,
                'count': count,
                'status': status
            })
            
            print(f"{status} {idx:2d}. {chapter:<50} {count:>4} chunks")
            
        except Exception as e:
            print(f"❌ ERROR checking {chapter}: {e}")
            results.append({
                'chapter': chapter,
                'count': 0,
                'status': '❌ ERROR'
            })
    
    # Summary
    print("\n" + "="*80)
    print("📈 COVERAGE SUMMARY")
    print("="*80)
    
    good_chapters = [r for r in results if r['count'] >= 5]
    sparse_chapters = [r for r in results if 2 <= r['count'] < 5]
    missing_chapters = [r for r in results if r['count'] < 2]
    
    print(f"\n✅ GOOD Coverage (≥5 chunks):   {len(good_chapters)}/14 chapters")
    for r in good_chapters:
        print(f"   - {r['chapter']} ({r['count']} chunks)")
    
    print(f"\n⚠️ SPARSE Coverage (2-4 chunks): {len(sparse_chapters)}/14 chapters")
    for r in sparse_chapters:
        print(f"   - {r['chapter']} ({r['count']} chunks)")
    
    print(f"\n❌ MISSING (0-1 chunks):         {len(missing_chapters)}/14 chapters")
    for r in missing_chapters[:5]:
        print(f"   - {r['chapter']}")
    if len(missing_chapters) > 5:
        print(f"   ... and {len(missing_chapters)-5} more")
    
    print(f"\nTotal Chunks Available: {total_chunks}")
    print(f"Chapters with Data: {chapters_with_data}/14 ({chapters_with_data/14*100:.1f}%)")
    
    # Recommendation
    print("\n" + "="*80)
    print("🎯 RECOMMENDATION")
    print("="*80)
    
    if chapters_with_data >= 12:
        recommendation = "✅ PROCEED - Excellent coverage, can generate full exam"
        action = "Generate full 14-chapter exam with confidence"
    elif chapters_with_data >= 8:
        recommendation = "⚠️ PROCEED WITH CAUTION - Good coverage but some gaps"
        action = "Generate exam with LLM fallback for missing chapters"
    elif chapters_with_data >= 5:
        recommendation = "⚠️ LIMITED - Partial coverage only"
        action = "Option 1: Generate with available chapters only\nOption 2: Wait for seeding to complete\nOption 3: Use LLM-only mode for missing chapters"
    else:
        recommendation = "❌ INSUFFICIENT DATA - Seeding required"
        action = "Wait for Qdrant seeding job to complete before generating"
    
    print(f"\n{recommendation}")
    print(f"\nRecommended Action:")
    print(f"{action}")
    
    # Save results
    with open('qdrant_coverage_report.json', 'w') as f:
        json.dump({
            'total_chapters': len(chapters),
            'chapters_with_data': chapters_with_data,
            'coverage_percentage': chapters_with_data/14*100,
            'total_chunks': total_chunks,
            'good_coverage': len(good_chapters),
            'sparse_coverage': len(sparse_chapters),
            'missing_coverage': len(missing_chapters),
            'results': results,
            'recommendation': recommendation,
            'action': action
        }, f, indent=2)
    
    print(f"\n✅ Coverage report saved to: qdrant_coverage_report.json")
    print("="*80 + "\n")

if __name__ == '__main__':
    check_qdrant_coverage()
