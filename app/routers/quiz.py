from fastapi import APIRouter, HTTPException
from app.models.quizmodels import QuizRequest, QuizResponse, QuizQuestionModel
from app.services.ragservice import HybridRAGService
from app.services.geminiservice import GeminiService
from app.config.prompts import get_quiz_prompt
from json_repair import repair_json
import json
import time

router = APIRouter()
rag_service = HybridRAGService()
gemini_service = GeminiService()

@router.post("/v1/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """
    Generate self-practice quiz with detailed explanations.
    """
    start_time = time.time()
    
    # 1. Retrieval
    # We broaden the query to get a good mix of concepts from the chapters
    query = f"{request.subject} {request.difficulty} practice questions key concepts {' '.join(request.chapters)}"
    
    filters = {
        "board": request.board,
        "class": request.class_num,
        "subject": request.subject
    }
    
    # Get context from RAG
    rag_result = rag_service.search(query, filters)
    
    # 2. Prompting
    prompt = get_quiz_prompt(
        context=rag_result['context'],
        count=request.numQuestions,
        difficulty=request.difficulty
    )
    
    # 3. Generation
    # ✅ FIX: Added 'await' here because GeminiService is now async
    try:
        response_text = await gemini_service.generate(prompt, temperature=0.5, max_tokens=2500)
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        raise HTTPException(500, "AI Service Unavailable")
    
    questions = []
    try:
        # Repair and Parse JSON
        clean_json = repair_json(response_text)
        questions_data = json.loads(clean_json)
        
        for q in questions_data:
            # --- ROBUSTNESS FIXES ---
            # 1. Map common LLM mistakes (e.g. "answer" instead of "correctAnswer")
            if 'answer' in q and 'correctAnswer' not in q:
                q['correctAnswer'] = q['answer']
            
            # 2. Inject defaults if missing
            if 'bloomsLevel' not in q: q['bloomsLevel'] = 'Apply'
            if 'marks' not in q: q['marks'] = 1
            if 'difficulty' not in q: q['difficulty'] = request.difficulty
            
            # 3. Critical Field Checks (Skip if missing)
            if 'text' not in q or 'options' not in q or 'correctAnswer' not in q:
                continue # Skip bad question
            
            # 4. Ensure explanation exists (Critical for Quiz)
            if 'explanation' not in q:
                q['explanation'] = f"The correct answer is {q['correctAnswer']}."

            q['sourcePage'] = q.get('sourcePage', 0)
            
            # Validate options
            if len(q.get('options', [])) == 4:
                questions.append(QuizQuestionModel(**q))
            
    except Exception as e:
        print(f"❌ Error parsing quiz: {e}")
        # Valid safe access to response_text since it was awaited above
        print(f"DEBUG LLM Output: {response_text[:500]}...") 
        raise HTTPException(500, "Failed to generate valid quiz questions.")

    # 4. Final Response Assembly
    blooms_dist = {}
    for q in questions:
        blooms_dist[q.bloomsLevel] = blooms_dist.get(q.bloomsLevel, 0) + 1

    return QuizResponse(
        questions=questions,
        totalMarks=len(questions),
        timeLimit=len(questions), # Rule of thumb: 1 min per MCQ
        bloomsDistribution=blooms_dist
    )