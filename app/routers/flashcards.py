from fastapi import APIRouter, HTTPException
from app.models.flashcardmodels import FlashcardRequest, FlashcardResponse, FlashcardModel
# ✅ USE QDRANT SERVICE
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.config.prompts import get_flashcard_prompt
from json_repair import repair_json
import json

router = APIRouter()
gemini_service = GeminiService()

@router.post("/v1/flashcards/generate", response_model=FlashcardResponse)
async def generate_flashcards(request: FlashcardRequest):
    query = f"{request.subject} {request.chapter} definitions formulas key concepts"
    filters = {"board": request.board, "class": request.class_num, "subject": request.subject}
    
    # ✅ QDRANT SEARCH (FIXED: Added await)
    rag_result = await qdrant_service.hybrid_search(query, filters, top_k=8)
    
    prompt = get_flashcard_prompt(rag_result['context'], request.cardCount)
    
    # Increased tokens
    response_text = await gemini_service.generate(prompt, temperature=0.3, max_tokens=2000)
    
    flashcards = []
    try:
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        clean_json = repair_json(clean_text)
        cards_data = json.loads(clean_json)
        
        # Unwrap dict
        if isinstance(cards_data, dict):
            found_list = False
            for k, v in cards_data.items():
                if isinstance(v, list):
                    cards_data = v
                    found_list = True
                    break
            if not found_list: cards_data = [cards_data]
        
        if isinstance(cards_data, dict): cards_data = [cards_data]
        if not isinstance(cards_data, list): cards_data = []

        for c in cards_data:
            if 'front' not in c:
                for k in ['term', 'question', 'concept', 'name', 'title']:
                    if k in c: c['front'] = c[k]; break
            if 'back' not in c:
                for k in ['definition', 'answer', 'explanation', 'formula', 'meaning', 'description']:
                    if k in c: c['back'] = c[k]; break
            
            if 'type' not in c: c['type'] = 'concept'
            c['sourcePage'] = c.get('sourcePage', 0)
            
            if 'front' in c and 'back' in c:
                flashcards.append(FlashcardModel(**c))
            
    except Exception as e:
        print(f"❌ Error parsing flashcards: {e}")
        raise HTTPException(500, "Failed to generate flashcards.")

    type_counts = {}
    for c in flashcards:
        type_counts[c.type] = type_counts.get(c.type, 0) + 1

    return FlashcardResponse(
        flashcards=flashcards,
        totalCards=len(flashcards),
        cardTypes=type_counts
    )