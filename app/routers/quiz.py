from fastapi import APIRouter, HTTPException
from app.models.quizmodels import QuizRequest, QuizResponse, QuizQuestionModel
# ✅ USE QDRANT SERVICE
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.prompts import get_quiz_prompt
from json_repair import repair_json
import json
import time

router = APIRouter()
gemini_service = GeminiService()

@router.post("/v1/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    start_time = time.time()
    
    query = f"{request.subject} {request.difficulty} practice questions key concepts {' '.join(request.chapters)}"
    filters = {
        "board": request.board,
        "class": request.class_num,
        "subject": request.subject
    }
    
    # ✅ QDRANT SEARCH (FIXED: Added await)
    rag_result = await qdrant_service.hybrid_search(query, filters, top_k=8)
    
    prompt = get_quiz_prompt(
        context=rag_result['context'],
        count=request.numQuestions,
        difficulty=request.difficulty
    )
    
    try:
        response_text = await gemini_service.generate(prompt, temperature=0.5, max_tokens=2500)
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        raise HTTPException(500, "AI Service Unavailable")
    
    questions = []
    try:
        clean_json = repair_json(response_text)
        questions_data = json.loads(clean_json)
        
        for q in questions_data:
            if 'answer' in q and 'correctAnswer' not in q:
                q['correctAnswer'] = q['answer']
            if 'bloomsLevel' not in q: q['bloomsLevel'] = 'Apply'
            if 'marks' not in q: q['marks'] = 1
            if 'difficulty' not in q: q['difficulty'] = request.difficulty
            
            if 'text' not in q or 'options' not in q or 'correctAnswer' not in q:
                continue 
            if 'explanation' not in q:
                q['explanation'] = f"The correct answer is {q['correctAnswer']}."

            q['sourcePage'] = q.get('sourcePage', 0)
            
            if len(q.get('options', [])) == 4:
                questions.append(QuizQuestionModel(**q))
            
    except Exception as e:
        print(f"❌ Error parsing quiz: {e}")
        raise HTTPException(500, "Failed to generate valid quiz questions.")

    blooms_dist = {}
    for q in questions:
        blooms_dist[q.bloomsLevel] = blooms_dist.get(q.bloomsLevel, 0) + 1

    return QuizResponse(
        questions=questions,
        totalMarks=len(questions),
        timeLimit=len(questions), 
        bloomsDistribution=blooms_dist
    )