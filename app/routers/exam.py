from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.exammodels import ExamRequest, ExamResponse, QuestionModel
from app.services.qdrant_service import qdrant_service
from app.services.geminiservice import GeminiService
from app.services.pdfgenerator import PDFGenerator
from app.config.prompts import get_exam_prompt
from app.config.settings import settings
from json_repair import repair_json
import json
import time
import asyncio
import re

router = APIRouter()
gemini_service = GeminiService()
pdf_generator = PDFGenerator()

# Constants
MAX_QUESTIONS_PER_BATCH = 5
FREE_TIER_BATCH_DELAY = 2  # Reduced wait time due to key rotation

def _calculate_distribution(total: int, percentages: dict) -> dict:
    """Convert percentages to exact question counts"""
    distribution = {}
    remaining = total
    for level, pct in percentages.items():
        count = int((pct / 100) * total)
        distribution[level] = count
        remaining -= count
    if remaining > 0:
        max_level = max(percentages, key=percentages.get)
        distribution[max_level] += remaining
    return distribution

def _normalize_options(options):
    """Aggressive option parser to handle malformed lists"""
    if isinstance(options, dict): return list(options.values())[:4]
    
    if isinstance(options, list):
        cleaned = [str(o).strip() for o in options if str(o).strip()]
        if len(cleaned) == 4: return cleaned
        
        # Handle cases where options are merged string
        combined = " ".join([str(o) for o in options])
        parts = re.split(r'(?:^|\s|\\n)(?:[A-Da-d]|[1-4])[\.\)]\s*', combined)
        split_cleaned = [p.strip() for p in parts if p.strip()]
        
        if len(split_cleaned) >= 2:
            return split_cleaned[:4]
            
        lines = [l.strip() for l in combined.split('\n') if l.strip()]
        if len(lines) >= 2: return lines[:4]

    return []

def _ensure_correct_answer(q_data: dict, options: list) -> bool:
    """Safety Net: Guarantees valid question structure."""
    # 1. Check explicit keys
    for k in ['correctAnswer', 'answer', 'correct', 'right_answer', 'correct_option', 'Answer']:
        if k in q_data and q_data[k]:
            q_data['correctAnswer'] = str(q_data[k])
            return True

    # 2. Auto-select first option if missing
    if options and len(options) >= 2:
        q_data['correctAnswer'] = options[0]
        q_data['explanation'] = q_data.get('explanation', '') + " (Auto-selected first option)"
        return True
    
    return False

@router.post("/v1/exam/generate", response_model=ExamResponse)
async def generate_exam(request: ExamRequest):
    start_time = time.time()
    distribution = _calculate_distribution(request.totalQuestions, request.bloomsDistribution)
    all_questions = []
    
    for level, count in distribution.items():
        if count == 0: continue
        
        remaining = count
        batch_num = 0
        
        while remaining > 0:
            if len(all_questions) > 0:
                # Slight delay to prevent bursting even with rotation
                await asyncio.sleep(FREE_TIER_BATCH_DELAY)

            batch_size = min(MAX_QUESTIONS_PER_BATCH, remaining)
            batch_num += 1
            
            print(f"   Generating {level} Batch {batch_num}: {batch_size} questions...")
            
            # 1. Retrieval (Qdrant)
            query = f"{request.subject} {level} questions {' '.join(request.chapters)}"
            filters = {
                "board": request.board, 
                "class": request.class_num, 
                "subject": request.subject
            }
            # Retrieve top 8 chunks to ensure enough context for multi-chapter
            rag_result = qdrant_service.hybrid_search(query, filters, top_k=8)
            
            # Traceability Metadata
            top_chunks = rag_result['chunks'][:5]
            chunk_ids = [c['id'] for c in top_chunks]
            # Handle RRF scores (which can be small) normalizing for display
            avg_confidence = sum(c.get('rerank_score', 0) for c in top_chunks) / len(top_chunks) if top_chunks else 0.0
            
            # 2. Prompting
            prompt = get_exam_prompt(rag_result['context'], level, batch_size, request.difficulty)
            
            try:
                # ---------------------------------------------------------
                # 🚨 CRITICAL FIX: ADAPTIVE TOKEN BUDGET
                # ---------------------------------------------------------
                
                # Complex questions (Apply/Analyze) need significantly more tokens
                # for scenarios, detailed options, and explanations.
                if level in ["Understand", "Apply", "Analyze", "Evaluate"]:
                    tokens_per_q = 800 
                else:
                    tokens_per_q = 500  # Remember/Create are usually shorter
                
                # Multi-chapter exams usually result in longer contexts and requires
                # the model to synthesize more information, increasing output length.
                chapter_overhead = 500 * len(request.chapters)
                
                # Calculate total estimated tokens needed
                estimated_tokens = (batch_size * tokens_per_q) + chapter_overhead + 1000
                
                # Cap at Gemini Flash limit (8192) to avoid API errors
                # Previously capped at 5000, which caused the truncation issue
                final_max_tokens = min(estimated_tokens, 8192)
                
                # print(f"      💰 Token Budget: {final_max_tokens}") # Debug print

                # 3. Generation
                response_text = await gemini_service.generate(
                    prompt, 
                    temperature=0.3,
                    max_tokens=final_max_tokens 
                )
                
                # 🔍 DEBUG: Log raw response for first batch to monitor
                if batch_num == 1:
                    print(f"\n{'='*60}")
                    print(f"🔍 DEBUG: Level={level}, Batch={batch_num}, MaxTokens={final_max_tokens}")
                    print(f"RAW RESPONSE (first 500 chars): {response_text[:500]}...")
                    print(f"{'='*60}\n")
                
                # 4. Parsing & Repair
                clean_text = response_text.replace("```json", "").replace("```", "")
                clean_json = repair_json(clean_text)
                questions_data = json.loads(clean_json)
                
                if isinstance(questions_data, dict): questions_data = [questions_data]
                
                valid_count_batch = 0
                for q_data in questions_data:
                    try:
                        # Normalize Options
                        q_data['options'] = _normalize_options(q_data.get('options', []))
                        
                        # Safety Net: Ensure answer exists
                        if not _ensure_correct_answer(q_data, q_data.get('options', [])):
                            print(f"    ⚠️ Skipping: No valid options/answer found.")
                            continue

                        # Enrich Data
                        q_data['bloomsLevel'] = level
                        q_data['difficulty'] = request.difficulty
                        q_data['marks'] = 1
                        q_data['ragChunkIds'] = chunk_ids
                        q_data['ragConfidence'] = round(avg_confidence, 4)
                        q_data['ragNumSources'] = len(top_chunks)
                        q_data['llmModel'] = settings.GEMINI_MODEL
                        q_data['qualityScore'] = min(1.0, avg_confidence * 1.1)
                        
                        if top_chunks:
                            q_data['sourcePage'] = top_chunks[0]['metadata'].get('page', 0)
                            q_data['sourceTextbook'] = top_chunks[0]['metadata'].get('textbook', 'NCERT')
                        
                        # Ensure exactly 4 options
                        options = q_data['options']
                        if len(options) >= 2:
                            while len(options) < 4:
                                options.append(f"Option {chr(65+len(options))}")
                            q_data['options'] = options[:4]
                            
                            all_questions.append(QuestionModel(**q_data))
                            valid_count_batch += 1
                        else:
                            print(f"    ⚠️ Skipping: Only {len(options)} options found.")
                            
                    except Exception as e:
                        print(f"    ⚠️ Parse Error inside question loop: {e}")
                        continue
                
                print(f"    ✅ Parsed {valid_count_batch}/{batch_size} questions")
                
            except Exception as e:
                print(f"❌ Batch Error: {e}")
            
            remaining -= batch_size

    # Final Verification
    actual_breakdown = {}
    total_marks = 0
    for q in all_questions:
        actual_breakdown[q.bloomsLevel] = actual_breakdown.get(q.bloomsLevel, 0) + 1
        total_marks += q.marks

    return ExamResponse(
        questions=all_questions,
        bloomsBreakdown=actual_breakdown,
        totalQuestions=len(all_questions),
        totalMarks=total_marks,
        generationTime=int((time.time() - start_time) * 1000)
    )

@router.post("/v1/exam/generate-pdf")
async def generate_exam_pdf(exam_data: dict):
    try:
        exam_id = exam_data.get('examId', f"exam_{int(time.time())}")
        pdf_path = pdf_generator.generate_exam_pdf(exam_id, exam_data)
        return FileResponse(pdf_path, media_type='application/pdf', filename=f"{exam_id}.pdf")
    except Exception as e:
        raise HTTPException(500, f"Failed to generate PDF: {str(e)}")