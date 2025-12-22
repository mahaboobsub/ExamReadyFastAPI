from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any  # <--- Added 'Any' here

class ConversationMessage(BaseModel):
    role: str # "user" or "model"
    text: str

class TutorRequest(BaseModel):
    query: str
    filters: Dict[str, Any]
    conversationHistory: List[ConversationMessage] = []
    mode: str = "student" # "student" or "teacher_sme"

class SourceChunk(BaseModel):
    page: int
    textbook: str
    text: str

class TutorResponse(BaseModel):
    response: str
    sources: List[SourceChunk]
    bloomsLevel: str
    confidenceScore: float