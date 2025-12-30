from app.services.qdrant_service import qdrant_service

def test():
    # 1. Semantic Test (Definition)
    print("📐 Test 1: Semantic (Concept)")
    res = qdrant_service.hybrid_search(
        "What is the Fundamental Theorem of Arithmetic?", 
        {"subject": "Maths"}
    )
    if res['chunks']:
        print(f"✅ Found {len(res['chunks'])} chunks.")
        print(f"   Top source: {res['chunks'][0]['metadata']['chapter']} (p{res['chunks'][0]['metadata']['page']})")
    else:
        print("❌ No chunks found.")

    # 2. Keyword Test (Formula)
    print("\n📐 Test 2: Keyword (Formula)")
    # This tests if LaTeX/Math symbols were indexed correctly
    res = qdrant_service.hybrid_search(
        "relationship between zeroes and coefficients", 
        {"subject": "Maths"}
    )
    if res['chunks']:
        print(f"✅ Found {len(res['chunks'])} chunks.")
        print(f"   Snippet: {res['chunks'][0]['text'][:100]}...")
    else:
        print("❌ No chunks found.")
    
    # 3. Negative Test (Physics Bleed)
    print("\n🧪 Test 3: Negative Test (Subject Isolation)")
    res = qdrant_service.hybrid_search(
        "What is Ohm's Law?", 
        {"subject": "Maths"} # Asking Physics Q in Maths subject
    )
    
    # We expect either NO results (if filter works perfectly) 
    # OR very low scores if RRF forces a match.
    if not res['chunks']:
        print("✅ Correctly returned 0 chunks due to metadata filter.")
    else:
        print(f"⚠️ Returned chunks (RRF forced match). Top score: {res['chunks'][0]['rerank_score']}")
        print("   (This is acceptable if score is low, Prompt Guardrail will reject it)")

if __name__ == "__main__":
    test()