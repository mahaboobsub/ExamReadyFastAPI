# from fastapi import APIRouter
# from app.models.tutormodels import TutorRequest, TutorResponse, SourceChunk
# from app.services.qdrant_service import qdrant_service  # ✅ CHANGED
# from app.services.geminiservice import GeminiService
# from app.config.prompts import get_tutor_prompt

# router = APIRouter()
# gemini_service = GeminiService()

# @router.post("/v1/tutor/answer", response_model=TutorResponse)
# async def tutor_answer(request: TutorRequest):
#     """
#     AI Tutor with Dual Mode (Student vs Teacher SME)
#     """
#     # 1. Retrieval
#     full_query = request.query
#     if request.conversationHistory:
#         last_msg = request.conversationHistory[-1]
#         last_text = last_msg.text if hasattr(last_msg, 'text') else last_msg.get('text', '')
#         full_query = f"{last_text} {request.query}"
        
#     # ✅ CHANGED: Use Qdrant
#     rag_result = qdrant_service.hybrid_search(full_query, request.filters, top_k=5)
    
#     # 2. Prompting
#     prompt = get_tutor_prompt(
#         query=request.query,
#         context=rag_result['context'],
#         history=request.conversationHistory,
#         mode=request.mode
#     )
    
#     # 3. Generation
#     max_tokens = 1500 
#     response_text = await gemini_service.generate(prompt, max_tokens=max_tokens)
    
#     # 4. Sources
#     sources = []
#     if rag_result.get('chunks'):
#         for chunk in rag_result['chunks'][:3]: 
#             sources.append(SourceChunk(
#                 page=chunk['metadata'].get('page', 0),
#                 textbook=chunk['metadata'].get('textbook', 'NCERT'),
#                 text=chunk['text'][:200] + "..."
#             ))

#     return TutorResponse(
#         response=response_text,
#         sources=sources,
#         bloomsLevel="Understand",
#         confidenceScore=0.95
#     )

from fastapi import APIRouter
from app.models.tutormodels import TutorRequest, TutorResponse, SourceChunk
# ✅ USE QDRANT SERVICE
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.prompts import get_tutor_prompt

router = APIRouter()
gemini_service = GeminiService()

@router.post("/v1/tutor/answer", response_model=TutorResponse)
async def tutor_answer(request: TutorRequest):
    """
    AI Tutor with Dual Mode (Student vs Teacher SME)
    """
    full_query = request.query
    if request.conversationHistory:
        last_msg = request.conversationHistory[-1]
        last_text = last_msg.text if hasattr(last_msg, 'text') else last_msg.get('text', '')
        full_query = f"{last_text} {request.query}"
        
    # ✅ QDRANT SEARCH (FIXED: Added await)
    rag_result = await qdrant_service.hybrid_search(full_query, request.filters, top_k=5)
    
    prompt = get_tutor_prompt(
        query=request.query,
        context=rag_result['context'],
        history=request.conversationHistory,
        mode=request.mode
    )
    
    # Increased tokens
    max_tokens = 1500 
    response_text = await gemini_service.generate(prompt, max_tokens=max_tokens)
    
    sources = []
    if rag_result.get('chunks'):
        for chunk in rag_result['chunks'][:3]: 
            sources.append(SourceChunk(
                page=chunk['metadata'].get('page', 0),
                textbook=chunk['metadata'].get('textbook', 'NCERT'),
                text=chunk['text'][:200] + "..."
            ))

    return TutorResponse(
        response=response_text,
        sources=sources,
        bloomsLevel="Understand",
        confidenceScore=0.95
    )