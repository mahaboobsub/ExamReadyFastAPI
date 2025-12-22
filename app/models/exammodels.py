from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExamRequest(BaseModel):
    board: str
    class_num: int = Field(..., alias="class")
    subject: str
    chapters: List[str]
    totalQuestions: int
    bloomsDistribution: Dict[str, int]
    difficulty: str

class QuestionModel(BaseModel):
    text: str
    type: str = "MCQ"
    options: List[str]
    correctAnswer: str
    explanation: str = ""
    bloomsLevel: str
    marks: int
    difficulty: str
    hasLatex: bool = False
    
    # --- Traceability Fields (Required for Node.js Deduplication) ---
    sourcePage: int = 0
    sourceTextbook: str = "Unknown"
    ragChunkIds: List[str] = []
    ragConfidence: float = 0.0
    ragNumSources: int = 0
    
    # --- LLM Metadata ---
    llmModel: str = "gemini-2.5-flash"
    llmTemperature: float = 0.3
    tokensInput: int = 0
    tokensOutput: int = 0
    qualityScore: float = 0.0

class ExamResponse(BaseModel):
    questions: List[QuestionModel]
    bloomsBreakdown: Dict[str, int]
    totalQuestions: int
    totalMarks: int
    generationTime: int