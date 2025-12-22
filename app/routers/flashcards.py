from fastapi import APIRouter, HTTPException
from app.models.flashcardmodels import FlashcardRequest, FlashcardResponse, FlashcardModel
from app.services.ragservice import HybridRAGService
from app.services.geminiservice import GeminiService
from app.config.prompts import get_flashcard_prompt
from json_repair import repair_json
import json

router = APIRouter()
rag_service = HybridRAGService()
gemini_service = GeminiService()

@router.post("/v1/flashcards/generate", response_model=FlashcardResponse)
async def generate_flashcards(request: FlashcardRequest):
    # 1. Retrieval
    query = f"{request.subject} {request.chapter} definitions formulas key concepts"
    filters = {"board": request.board, "class": request.class_num, "subject": request.subject}
    rag_result = rag_service.search(query, filters)
    
    # 2. Prompting
    prompt = get_flashcard_prompt(rag_result['context'], request.cardCount)
    
    # 3. Generation
    response_text = await gemini_service.generate(prompt, temperature=0.3, max_tokens=2000)
    
    flashcards = []
    try:
        # Pre-clean markdown
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Repair JSON
        clean_json = repair_json(clean_text)
        cards_data = json.loads(clean_json)
        
        # Handle dict wrapper (e.g. {"flashcards": [...]})
        if isinstance(cards_data, dict):
            found_list = False
            for k, v in cards_data.items():
                if isinstance(v, list):
                    cards_data = v
                    found_list = True
                    break
            # If no list found in values, maybe the dict itself is a single card?
            if not found_list:
                cards_data = [cards_data]
        
        # Handle Single Object (LLM forgot list brackets)
        if isinstance(cards_data, dict):
             cards_data = [cards_data]
             
        # Handle if it's still not a list (shouldn't happen)
        if not isinstance(cards_data, list):
            print(f"⚠️ Warning: LLM returned non-list structure: {type(cards_data)}")
            cards_data = []

        for c in cards_data:
            # --- ROBUST KEY MAPPING ---
            # Map Front
            if 'front' not in c:
                for k in ['term', 'question', 'concept', 'name', 'title']:
                    if k in c: c['front'] = c[k]; break
            
            # Map Back
            if 'back' not in c:
                for k in ['definition', 'answer', 'explanation', 'formula', 'meaning', 'description']:
                    if k in c: c['back'] = c[k]; break
            
            # Defaults
            if 'type' not in c: c['type'] = 'concept'
            c['sourcePage'] = c.get('sourcePage', 0)
            
            if 'front' in c and 'back' in c:
                flashcards.append(FlashcardModel(**c))
            
    except Exception as e:
        print(f"❌ Error parsing flashcards: {e}")
        print(f"DEBUG RAW OUTPUT: {response_text[:500]}...") 
        raise HTTPException(500, "Failed to generate flashcards.")

    # Log empty result for debugging
    if not flashcards:
        print(f"⚠️ Zero flashcards generated. Raw output start:\n{response_text[:600]}")

    type_counts = {}
    for c in flashcards:
        type_counts[c.type] = type_counts.get(c.type, 0) + 1

    return FlashcardResponse(
        flashcards=flashcards,
        totalCards=len(flashcards),
        cardTypes=type_counts
    )