from typing import Dict, List

# Constants
BOARD_QUALITY_THRESHOLD = 0.85
CUSTOM_QUALITY_THRESHOLD = 0.70

def calculate_quality_score(question: Dict) -> float:
    """
    Calculate question quality (0.0 - 1.0)
    Formula: 0.4*RAG + 0.2*Bloom + 0.15*Style + 0.15*Complete + 0.1*Valid
    """
    # 1. RAG Confidence (40%)
    rag_conf = question.get("ragConfidence", 0.0)
    if rag_conf == 0.0: # Fallback based on source
        src = question.get("sourceTag", "")
        if "PYQ" in src: rag_conf = 0.90
        elif "CBSE_SAMPLE" in src: rag_conf = 0.85
        else: rag_conf = 0.70

    # 2. Bloom's Alignment (20%)
    # Simplified: Assume alignment if generated correctly
    blooms_score = 1.0 

    # 3. CBSE Style (15%)
    # Simplified: High if PYQ
    style_score = 0.9 if "PYQ" in question.get("sourceTag", "") else 0.5

    # 4. Completeness (15%)
    required = ["text", "bloomsLevel", "marks"]
    if question.get("type") != "CASE_BASED":
        required.extend(["correctAnswer", "explanation"])
    
    present = sum(1 for k in required if question.get(k))
    completeness = present / len(required)

    # 5. Answer Validity (10%)
    validity = 1.0
    if question.get("type") == "MCQ":
        opts = question.get("options", [])
        ans = question.get("correctAnswer", "").lower().strip()
        if not opts or not ans: 
            validity = 0.0
        else:
            # Check if answer is in options
            validity = 1.0 if any(ans in o.lower() for o in opts) else 0.0

    score = (
        0.40 * rag_conf +
        0.20 * blooms_score +
        0.15 * style_score +
        0.15 * completeness +
        0.10 * validity
    )
    
    return round(score, 4)