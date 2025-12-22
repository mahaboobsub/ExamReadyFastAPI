from fastapi import APIRouter
from app.models.tutormodels import TutorRequest, TutorResponse, SourceChunk
from app.services.ragservice import HybridRAGService
from app.services.geminiservice import GeminiService
from app.config.prompts import get_tutor_prompt

router = APIRouter()
rag_service = HybridRAGService()
gemini_service = GeminiService()

@router.post("/v1/tutor/answer", response_model=TutorResponse)
async def tutor_answer(request: TutorRequest):
    """
    AI Tutor with Dual Mode (Student vs Teacher SME)
    """
    # 1. Retrieval
    # Add context from history if needed (simple concatenation for now)
    full_query = request.query
    if request.conversationHistory:
        # Check if history elements are objects or dicts (Pydantic compat)
        last_msg = request.conversationHistory[-1]
        last_text = last_msg.text if hasattr(last_msg, 'text') else last_msg.get('text', '')
        full_query = f"{last_text} {request.query}"
        
    rag_result = rag_service.search(full_query, request.filters)
    
    # 2. Prompting (Mode Switching)
    prompt = get_tutor_prompt(
        query=request.query,
        context=rag_result['context'],
        history=request.conversationHistory,
        mode=request.mode
    )
    
    # 3. Generation
    # ✅ FIX: Increased to 1500 to prevent cutoff sentences
    max_tokens = 1500 
    
    response_text = await gemini_service.generate(prompt, max_tokens=max_tokens)
    
    # 4. Sources
    sources = []
    # Guard clause in case no chunks were found
    if rag_result.get('chunks'):
        for chunk in rag_result['chunks'][:3]: # Top 3 sources
            sources.append(SourceChunk(
                page=chunk['metadata'].get('page', 0),
                textbook=chunk['metadata'].get('textbook', 'NCERT'),
                text=chunk['text'][:200] + "..."
            ))

    return TutorResponse(
        response=response_text,
        sources=sources,
        bloomsLevel="Understand", # Simplified for MVP
        confidenceScore=0.95 # Mock for now
    )