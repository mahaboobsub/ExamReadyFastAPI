from pydantic import BaseModel, Field
from typing import List, Dict

class FlashcardRequest(BaseModel):
    board: str
    class_num: int = Field(..., alias="class")
    subject: str
    chapter: str # Single chapter focus
    cardCount: int = Field(..., ge=5, le=50)

class FlashcardModel(BaseModel):
    type: str # "definition", "concept", "formula", "example"
    front: str
    back: str
    sourcePage: int = 0
    hasLatex: bool = False

class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardModel]
    totalCards: int
    cardTypes: Dict[str, int]