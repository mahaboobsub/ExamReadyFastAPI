from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
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
    all_questions = []
    seen_texts = set()

    # 1. Calculate Per-Chapter Quota to ensure balance
    chapter_count = len(request.chapters)
    if chapter_count == 0:
        raise HTTPException(400, "No chapters provided")
        
    base_per_chapter = request.totalQuestions // chapter_count
    remainder = request.totalQuestions % chapter_count
    
    print(f"🎯 Target: {request.totalQuestions} Questions across {chapter_count} Chapters (~{base_per_chapter}/ch)")

    # 2. Iterate Chapters (Fixes Mono-Topic Issue)
    # 2. Iterate Chapters (Single Batch per Chapter)
    for ch_idx, chapter in enumerate(request.chapters):
        # Distribute remainder
        target_count = base_per_chapter + (1 if ch_idx < remainder else 0)
        if target_count == 0: continue

        # Calculate local distribution string for prompt
        local_dist = _calculate_distribution(target_count, request.bloomsDistribution)
        dist_desc = ", ".join([f"{v} {k}" for k,v in local_dist.items() if v > 0])
        
        print(f"\n📘 Processing Chapter: {chapter} (Target: {target_count}, Mix: {dist_desc})")
        
        # 1. Retrieval (Specific to Chapter)
        # Query asks for "Mixed Level" implicitly by not specifying one
        query = f"{request.subject} objective questions about {chapter} concepts"
        filters = {
            "board": request.board, 
            "subject": request.subject,
        }
        
        # Using top_k=6 for sufficient context
        rag_result = await qdrant_service.hybrid_search(query, filters, top_k=6)
        top_chunks = rag_result['chunks'][:4]
        input_context = rag_result['context']
        
        chunk_ids = [c['id'] for c in top_chunks]
        avg_confidence = sum(c.get('rerank_score', 0) for c in top_chunks) / len(top_chunks) if top_chunks else 0.0

        # 2. Prompting
        # We ask for "Varied" levels and instruct model to label correctly
        sys_prompt = f"""
        You are an expert CBSE Question Setter.
        Topic: {chapter}
        Total Questions: {target_count}
        
        REQUIRED DISTRIBUTION: {dist_desc}
        
        Context:
        {input_context}
        
        Task:
        1. Generate {target_count} unique Multiple Choice Questions (MCQs) solely based on '{chapter}'.
        2. Strictly follow the requested distribution (e.g. if I asked for 1 Analyze, ensure one question is analytical).
        3. In the JSON output, set "bloomsLevel" to the SPECIFIC level of that question (e.g. "Remember", "Apply"), do NOT put "Mixed".
        """
        
        # We pass "Varied" to get_exam_prompt, but our sys_prompt overrides the instructions
        user_prompt = get_exam_prompt(rag_result['context'], "Varied", target_count, request.difficulty)
        full_prompt = sys_prompt + "\n" + user_prompt

        try:
            # Token Budget
            # Mixed batch needs generous tokens
            final_max_tokens = min((target_count * 800) + 1000, 8192)

            # 3. Generation
            response_text = await gemini_service.generate(
                full_prompt, 
                temperature=0.4, 
                max_tokens=final_max_tokens 
            )
            
            # 4. Parsing
            clean_text = response_text.replace("```json", "").replace("```", "")
            clean_json = repair_json(clean_text)
            questions_data = json.loads(clean_json)
            
            if isinstance(questions_data, dict): questions_data = [questions_data]
            
            valid_count_batch = 0
            for q_data in questions_data:
                try:
                    # Deduplication
                    q_text = q_data.get('text', '').strip()
                    if not q_text or len(q_text) < 10: continue
                    
                    is_dup = False
                    for existing in seen_texts:
                        if q_text in existing or existing in q_text:
                            is_dup = True
                            break
                    if is_dup:
                        print(f"    ⚠️ Skipping Duplicate: {q_text[:30]}...")
                        # Try to salvage if partially duplicative? No, skip safety.
                        continue
                        
                    seen_texts.add(q_text)

                    # Normalize Options
                    q_data['options'] = _normalize_options(q_data.get('options', []))
                    if not _ensure_correct_answer(q_data, q_data.get('options', [])): continue

                    # Enrich
                    b_level = q_data.get('bloomsLevel', 'Remember')
                    # Validation: Ensure it's a valid level string
                    if b_level not in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]:
                         b_level = "Apply" # Default fallback
                    q_data['bloomsLevel'] = b_level
                    
                    # Difficulty Mapping
                    if b_level in ["Remember", "Understand"]: q_data['difficulty'] = "Easy"
                    elif b_level == "Apply": q_data['difficulty'] = "Medium"
                    else: q_data['difficulty'] = "Hard"
                    
                    q_data['chapter'] = chapter
                    q_data['marks'] = 1
                    q_data['ragChunkIds'] = chunk_ids
                    q_data['ragConfidence'] = round(avg_confidence, 4)
                    q_data['qualityScore'] = min(1.0, avg_confidence * 1.1)
                    
                    options = q_data['options']
                    while len(options) < 4:
                        options.append(f"Option {chr(65+len(options))}")
                    q_data['options'] = options[:4]
                        
                    all_questions.append(QuestionModel(**q_data))
                    valid_count_batch += 1
                        
                except Exception as e:
                    print(f"    ⚠️ Parse Error: {e}")
                    continue
            
            print(f"    ✅ Parsed {valid_count_batch}/{target_count} questions for {chapter}")
            
        except Exception as e:
            print(f"❌ Batch Error ({chapter}): {e}")
        
        # Small delay between chapters
        await asyncio.sleep(1)
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
        print(f"❌ PDF Gen Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to generate PDF: {str(e)}")

@router.post("/v1/exam/generate-answer-key")
async def generate_answer_key_pdf(exam_data: dict):
    try:
        exam_id = exam_data.get('examId', f"exam_{int(time.time())}")
        pdf_path = pdf_generator.generate_teacher_pdf(exam_id, exam_data)
        return FileResponse(pdf_path, media_type='application/pdf', filename=f"{exam_id}_answer_key.pdf")
    except Exception as e:
        print(f"❌ Answer Key Gen Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to generate Answer Key: {str(e)}")

# --- NEW V1 BOARD EXAM ENDPOINT ---
from app.services.llm_exam_generator import LLMExamGenerator

class BoardExamRequest(BaseModel):
    board: str = "CBSE"
    class_num: int = 10
    subject: str = "Mathematics"
    chapters: Optional[List[str]] = None

@router.post("/v1/exam/generate-board", tags=["V1 Board"])
async def generate_board_exam(
    request: BoardExamRequest,
    x_internal_key: str = Header(None, alias="X-Internal-Key")
):
    """
    Generate FULL CBSE Board Exam (Sections A-E) using RAG + LLM.
    Strictly follows 2025-26 Pattern.
    """
    if x_internal_key != "dev_secret_key_12345":
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        generator = LLMExamGenerator()
        exam = await generator.generate_cbse_board_exam(
            board=request.board,
            class_num=request.class_num,
            subject=request.subject,
            chapters=request.chapters
        )
        
        # Save backup to avoid data loss on timeout
        try:
            with open("latest_generated_board_exam.json", "w", encoding="utf-8") as f:
                json.dump(exam, f, indent=2)
            print("✅ Backup saved to latest_generated_board_exam.json")
        except Exception as e:
            print(f"⚠️ Failed to save backup: {e}")

        return {
            "success": True,
            "type": "board_exam_v1",
            "exam": exam
        }
    except Exception as e:
        print(f"❌ Board Gen Error: {e}")
        raise HTTPException(500, f"Error generating board exam: {str(e)}")