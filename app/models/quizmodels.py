from pydantic import BaseModel, Field
from typing import List, Dict

class QuizRequest(BaseModel):
    board: str
    class_num: int = Field(..., alias="class")
    subject: str
    chapters: List[str]
    numQuestions: int = Field(..., ge=5, le=20, description="Number of questions (5-20)")
    difficulty: str = "Medium"

class QuizQuestionModel(BaseModel):
    text: str
    type: str = "MCQ"
    options: List[str]
    correctAnswer: str
    explanation: str # Critical for quizzes
    bloomsLevel: str
    marks: int = 1
    difficulty: str
    sourcePage: int = 0
    hasLatex: bool = False

class QuizResponse(BaseModel):
    questions: List[QuizQuestionModel]
    totalMarks: int
    timeLimit: int # Recommended time in minutes
    bloomsDistribution: Dict[str, int]