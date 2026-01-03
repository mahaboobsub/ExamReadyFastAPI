"""
Solution Page Detection using Keyword Matching
Automatically detects if a page contains questions or solutions
"""
from typing import List, Tuple


# Keywords that indicate a solution/marking scheme page
SOLUTION_KEYWORDS = [
    # Marking scheme indicators
    "marking scheme",
    "ms_x_mathematics",
    "ms_x_maths",
    "marking instructions",
    "answer key",
    "answer sheet",
    
    # Solution indicators
    "sol.",
    "solution:",
    "solution :",
    "solutions:",
    "expected answer",
    "expected outcomes",
    "sample answer",
    "model answer",
    
    # Examiner instructions
    "strictly confidential",
    "for evaluator",
    "for examiner",
    "marks awarded",
    "award marks",
    "full marks",
    "step marking",
    
    # Hindi equivalents (in case some remain)
    "अंक योजना",
    "उत्तर कुंजी",
]

# Keywords that strongly indicate question pages
QUESTION_KEYWORDS = [
    "general instructions",
    "read the following",
    "attempt all questions",
    "time allowed",
    "maximum marks",
    "section a",
    "section b",
    "section c",
    "section d",
    "section e",
    "q.no.",
    "question no",
]


def detect_content_type(page_text: str, page_num: int = 0) -> str:
    """
    Detect if page contains questions or solutions
    
    Args:
        page_text: Text content of the page
        page_num: Page number (optional, for heuristics)
        
    Returns:
        "question" or "solution"
    """
    page_text_lower = page_text.lower()
    
    # Score-based detection
    solution_score = 0
    question_score = 0
    
    # Check for solution keywords
    for keyword in SOLUTION_KEYWORDS:
        if keyword.lower() in page_text_lower:
            solution_score += 2
    
    # Check for question keywords
    for keyword in QUESTION_KEYWORDS:
        if keyword.lower() in page_text_lower:
            question_score += 1
    
    # Additional heuristics
    
    # High density of "Sol." indicates solution page
    sol_count = page_text_lower.count("sol.")
    if sol_count > 3:
        solution_score += 3
    
    # Presence of step-by-step marking
    if "step" in page_text_lower and ("mark" in page_text_lower or "½" in page_text):
        solution_score += 2
    
    # Award/marks indicators
    if page_text_lower.count("mark") > 5:
        solution_score += 1
    
    # OR indicators for multiple correct answers (common in MS)
    if page_text_lower.count(" or ") > 5:
        solution_score += 2
    
    # Question number patterns (Q.1, Q.2, etc.)
    import re
    question_patterns = len(re.findall(r'q\.?\s*\d+', page_text_lower))
    if question_patterns > 5:
        question_score += 2
    
    # Make decision
    if solution_score > question_score:
        return "solution"
    
    return "question"


def detect_content_type_with_confidence(page_text: str, page_num: int = 0) -> Tuple[str, float]:
    """
    Detect content type with confidence score
    
    Args:
        page_text: Text content of the page
        page_num: Page number
        
    Returns:
        Tuple of (content_type, confidence)
    """
    page_text_lower = page_text.lower()
    
    solution_score = 0
    question_score = 0
    
    # Count keyword matches
    for keyword in SOLUTION_KEYWORDS:
        if keyword.lower() in page_text_lower:
            solution_score += 2
    
    for keyword in QUESTION_KEYWORDS:
        if keyword.lower() in page_text_lower:
            question_score += 1
    
    # Calculate confidence
    total_score = solution_score + question_score
    if total_score == 0:
        return "question", 0.5  # Default to question with low confidence
    
    if solution_score > question_score:
        confidence = solution_score / total_score
        return "solution", min(confidence, 0.99)
    else:
        confidence = question_score / total_score
        return "question", min(confidence, 0.99)


def is_likely_marking_scheme_file(filename: str) -> bool:
    """
    Check if filename suggests it's a marking scheme
    
    Args:
        filename: Name of the PDF file
        
    Returns:
        True if likely a marking scheme file
    """
    filename_lower = filename.lower()
    
    ms_indicators = [
        "_ms",
        "_ms_",
        "ms_",
        "_marking",
        "marking_scheme",
        "markingscheme",
        "answer_key",
        "answerkey",
        "_solutions",
    ]
    
    for indicator in ms_indicators:
        if indicator in filename_lower:
            return True
    
    return False
