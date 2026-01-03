from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from enum import Enum

# --- ENUMS ---
class GenerationMode(str, Enum):
    BOARD = "board"
    CUSTOM = "custom"
    PRACTICE = "practice"

class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    MIXED = "Mixed"

class GenerationMethod(str, Enum):
    PRE_GENERATED = "pre-generated" # Qdrant only
    CACHED = "cached"               # Redis
    REAL_TIME = "real-time"         # Qdrant + LLM Fallback

# --- REQUEST MODELS ---

class BoardExamRequest(BaseModel):
    template_id: str = Field(..., description="Locked Template ID", pattern=r"^CBSE_\d{2}_[A-Z]+_BOARD_\d{4}$")

class PracticeExamRequest(BaseModel):
    template_id: str = Field(..., description="Locked Template ID for Student", pattern=r"^CBSE_\d{2}_[A-Z]+_BOARD_\d{4}$")

class CustomExamRequest(BaseModel):
    template_id: str
    chapters: List[str] = Field(..., min_items=1, max_items=5)
    chapter_weightage: Dict[str, float]
    difficulty: Difficulty = Difficulty.MIXED
    focus_topics: Optional[List[str]] = []

    @validator('chapter_weightage')
    def validate_weightage(cls, v):
        if abs(sum(v.values()) - 100) > 0.5:
            raise ValueError(f"Weights must sum to 100%, got {sum(v.values())}%")
        return v

# --- RESPONSE MODELS ---

class QuestionV2(BaseModel):
    id: str
    text: str
    type: str # MCQ, VSA, SA, LA, CASE_BASED
    section: str
    options: Optional[List[str]] = None
    
    # Metadata
    bloomsLevel: str
    marks: int
    difficulty: str
    chapter: str
    subtopic: Optional[str] = None
    
    # Teacher Only Fields (Removed for students)
    correctAnswer: Optional[str] = None
    explanation: Optional[str] = None
    
    # Quality & Source
    sourceTag: Optional[str] = ""
    qualityScore: Optional[float] = 0.0
    usageCount: Optional[int] = 0
    
    hasLatex: bool = False
    hasDiagram: bool = False

class DualPDFResponse(BaseModel):
    exam_id: str
    mode: GenerationMode
    exam_pdf_url: str
    answer_key_pdf_url: str
    total_marks: int
    total_questions: int
    chapters_covered: List[str]
    generation_method: GenerationMethod
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: int
    quality_score: float
    cache_key: Optional[str] = None

class PracticeExamResponse(BaseModel):
    exam_id: str
    questions: List[QuestionV2] # Answers will be removed by logic
    total_marks: int
    duration_minutes: int