from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CBSETemplate:
    """CBSE Exam Template Structure"""
    pattern_id: str
    board: str
    class_num: int
    subject: str
    pattern_type: str
    total_marks: int
    duration_minutes: int
    sections: List[Dict]
    overall_blooms: Dict[str, int]
    applicable_chapters: List[str]
    chapter_weightage: Dict[str, int] = field(default_factory=dict)
    is_locked: bool = True

# --- DEFINITIONS ---

# ✅ UPDATED: Official 2025-26 Pattern for Class 10 Maths
CBSE_10_MATHS_BOARD_2025 = CBSETemplate(
    pattern_id="CBSE_10_MATHS_BOARD_2025",
    board="CBSE",
    class_num=10,
    subject="Mathematics",
    pattern_type="board_exam",
    total_marks=80,
    duration_minutes=180,
    sections=[
        # Section A: 20 Questions (18 MCQ + 2 Assertion-Reason)
        {"code": "A", "name": "Section A - Objective", "question_count": 20, "marks_per_question": 1, "question_type": "MCQ", "sub_types": {"MCQ": 18, "ASSERTION_REASON": 2}},
        
        # Section B: 5 Questions (VSA) - Updated from 6
        {"code": "B", "name": "Section B - Very Short Answer", "question_count": 5, "marks_per_question": 2, "question_type": "VSA"},
        
        # Section C: 6 Questions (SA) - Updated from 7
        {"code": "C", "name": "Section C - Short Answer", "question_count": 6, "marks_per_question": 3, "question_type": "SA"},
        
        # Section D: 4 Questions (LA) - Updated from 3
        {"code": "D", "name": "Section D - Long Answer", "question_count": 4, "marks_per_question": 5, "question_type": "LA"},
        
        # Section E: 3 Questions (Case-Based)
        {"code": "E", "name": "Section E - Case-Based", "question_count": 3, "marks_per_question": 4, "question_type": "CASE_BASED"}
    ],
    overall_blooms={
        "Remember": 20, "Understand": 25, "Apply": 30, "Analyze": 20, "Evaluate": 5
    },
    applicable_chapters=[
        "Real Numbers", "Polynomials", "Pair of Linear Equations in Two Variables", 
        "Quadratic Equations", "Arithmetic Progressions", "Triangles", 
        "Coordinate Geometry", "Introduction to Trigonometry", "Some Applications of Trigonometry", 
        "Circles", "Areas Related to Circles", "Surface Areas and Volumes", 
        "Statistics", "Probability"
    ],
    chapter_weightage={
        "Real Numbers": 6,
        "Polynomials": 5, # Approx breakdown of Algebra (20)
        "Pair of Linear Equations in Two Variables": 5,
        "Quadratic Equations": 5,
        "Arithmetic Progressions": 5,
        "Coordinate Geometry": 6,
        "Triangles": 8, # Approx breakdown of Geometry (15)
        "Circles": 7,
        "Introduction to Trigonometry": 6, # Approx breakdown of Trig (12)
        "Some Applications of Trigonometry": 6,
        "Areas Related to Circles": 5, # Approx breakdown of Mensuration (10)
        "Surface Areas and Volumes": 5,
        "Statistics": 6, # Approx breakdown of Stats & Prob (11)
        "Probability": 5
    }
)

# Keep Science for reference
CBSE_10_SCIENCE_BOARD_2025 = CBSETemplate(
    pattern_id="CBSE_10_SCIENCE_BOARD_2025",
    board="CBSE",
    class_num=10,
    subject="Science",
    pattern_type="board_exam",
    total_marks=80,
    duration_minutes=180,
    sections=[
        {"code": "A", "name": "Objective", "question_count": 20, "marks_per_question": 1, "question_type": "MCQ"},
        {"code": "B", "name": "VSA", "question_count": 6, "marks_per_question": 2, "question_type": "VSA"},
        {"code": "C", "name": "SA", "question_count": 7, "marks_per_question": 3, "question_type": "SA"},
        {"code": "D", "name": "LA", "question_count": 3, "marks_per_question": 5, "question_type": "LA"},
        {"code": "E", "name": "Case", "question_count": 3, "marks_per_question": 4, "question_type": "CASE_BASED"}
    ],
    overall_blooms={"Remember": 20, "Understand": 25, "Apply": 30, "Analyze": 20, "Evaluate": 5},
    applicable_chapters=["Chemical Reactions and Equations", "Acids Bases and Salts", "Metals and Non-Metals", "Life Processes", "Light", "Electricity"]
)

# Registry
TEMPLATES = {
    "CBSE_10_SCIENCE_BOARD_2025": CBSE_10_SCIENCE_BOARD_2025,
    "CBSE_10_MATHS_BOARD_2025": CBSE_10_MATHS_BOARD_2025
}

def get_template(template_id: str) -> CBSETemplate:
    if template_id not in TEMPLATES:
        raise ValueError(f"Template '{template_id}' not found.")
    return TEMPLATES[template_id]