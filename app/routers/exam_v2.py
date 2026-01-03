from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
import time
import os
import uuid

# ✅ FIXED IMPORTS: Using V2 models
from app.models.exam_models_v2 import (
    BoardExamRequest, 
    CustomExamRequest, 
    PracticeExamRequest,
    DualPDFResponse,
    PracticeExamResponse,
    QuestionV2,
    GenerationMode,
    GenerationMethod
)
from app.services.board_exam_generator import board_exam_generator
from app.services.custom_exam_generator import custom_exam_generator
from app.services.pdfgenerator import pdf_generator
from app.config.settings import settings

router = APIRouter(prefix="/v2/exam", tags=["Exam Generation V2"])

# --- Security Dependency ---
async def verify_internal_key(x_internal_key: str = Header(...)):
    if x_internal_key != settings.X_INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Invalid Internal Key")
    return x_internal_key

# --- ENDPOINT 1: TEACHER BOARD EXAM ---
@router.post("/teacher/board", response_model=DualPDFResponse)
async def generate_teacher_board_exam(
    request: BoardExamRequest,
    _auth: str = Depends(verify_internal_key)
):
    """
    Generates a strict CBSE Board Exam (PDF + Key).
    No LLM used. Pure Qdrant retrieval.
    """
    try:
        start_time = time.time()
        print(f"\n[API] POST /v2/exam/teacher/board")
        print(f"[API] Template: {request.template_id}")

        # 1. Generate (Qdrant Only)
        exam_data = await board_exam_generator.generate(request.template_id)
        
        # 2. Generate PDFs
        # pdfgenerator returns a tuple: (student_filename, teacher_filename)
        student_fname, teacher_fname = pdf_generator.generate_dual_pdfs(exam_data)
        
        # 3. Format URLs
        exam_url = f"/static/pdfs/{student_fname}"
        key_url = f"/static/pdfs/{teacher_fname}"

        # 4. Map questions to V2 Model safely
        # FIXED: Explicit field mapping with validation
        questions_v2 = []
        for q in exam_data['questions']:
            try:
                question_v2 = QuestionV2(
                    id=q.get('id', ''),
                    text=q.get('text', ''),
                    type=q.get('type', 'MCQ'),
                    section=q.get('section', 'A'),
                    options=q.get('options', []),
                    bloomsLevel=q.get('bloomsLevel', 'Understand'),
                    marks=q.get('marks', 1),
                    difficulty=q.get('difficulty', 'Medium'),
                    chapter=q.get('chapter', 'Unknown'),
                    subtopic=q.get('subtopic'),
                    correctAnswer=q.get('correctAnswer'),
                    explanation=q.get('explanation'),
                    sourceTag=q.get('sourceTag', ''),
                    qualityScore=q.get('qualityScore', 0.0),
                    hasLatex=q.get('hasLatex', False),
                    hasDiagram=q.get('hasDiagram', False)
                )
                questions_v2.append(question_v2)
            except Exception as qe:
                print(f"⚠️ Skipping invalid question: {qe}")

        return DualPDFResponse(
            exam_id=exam_data['exam_id'],
            mode=GenerationMode.BOARD,
            total_marks=exam_data['total_marks'],
            total_questions=len(exam_data['questions']),
            chapters_covered=exam_data.get('chapters_covered', []),
            exam_pdf_url=exam_url,
            answer_key_pdf_url=key_url,
            generation_method=GenerationMethod.PRE_GENERATED,
            latency_ms=exam_data['latency_ms'],
            quality_score=0.0 # Placeholder or calculate if available
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- ENDPOINT 2: TEACHER CUSTOM EXAM ---
@router.post("/teacher/custom", response_model=DualPDFResponse)
async def generate_teacher_custom_exam(
    request: CustomExamRequest,
    _auth: str = Depends(verify_internal_key)
):
    """
    Generates a Custom Exam (Chapter selection).
    Uses Redis Cache -> Qdrant -> LLM Fallback.
    """
    try:
        # 1. Generate (Hybrid)
        exam_data = await custom_exam_generator.generate(request.dict())
        
        # 2. Generate PDFs (If not cached logic handles it, or regen here)
        if "exam_pdf_url" not in exam_data:
            student_fname, teacher_fname = pdf_generator.generate_dual_pdfs(exam_data)
            exam_data["exam_pdf_url"] = f"/static/pdfs/{student_fname}"
            exam_data["answer_key_pdf_url"] = f"/static/pdfs/{teacher_fname}"
            
        # 3. Flatten questions for response model (Custom gen returns sections dict)
        # FIXED: Handle both sections dict and questions list structures
        all_qs_v2 = []

        if isinstance(exam_data.get('sections'), dict):
            for sec_qs in exam_data['sections'].values():
                for q in sec_qs:
                    try:
                        all_qs_v2.append(QuestionV2(**q))
                    except Exception as qe:
                        print(f"⚠️ Skipping invalid question: {qe}")
        elif isinstance(exam_data.get('questions'), list):
            for q in exam_data['questions']:
                try:
                    all_qs_v2.append(QuestionV2(**q))
                except Exception as qe:
                    print(f"⚠️ Skipping invalid question: {qe}")
        else:
            print("⚠️ No valid question structure found in exam_data")

        return DualPDFResponse(
            exam_id=exam_data['exam_id'],
            mode=GenerationMode.CUSTOM,
            total_marks=exam_data['total_marks'],
            total_questions=exam_data['total_questions'],
            chapters_covered=exam_data['chapters_covered'],
            exam_pdf_url=exam_data['exam_pdf_url'],
            answer_key_pdf_url=exam_data['answer_key_pdf_url'],
            generation_method=exam_data['generation_method'],
            cost_usd=exam_data.get('cost_usd', 0.0),
            latency_ms=exam_data['latency_ms'],
            quality_score=exam_data.get('quality_score', 0.0),
            cache_key=exam_data.get('cache_key')
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3: STUDENT PRACTICE ---
@router.post("/student/practice", response_model=PracticeExamResponse)
async def generate_student_practice(
    request: PracticeExamRequest,
    _auth: str = Depends(verify_internal_key)
):
    """
    Student Practice Mode.
    Strict Rules: No LLM, No Answers in response, JSON Only.
    """
    try:
        # 1. Reuse Board Generator (Strict Retrieval)
        exam_data = await board_exam_generator.generate(request.template_id)
        
        # 2. STRIP ANSWERS (Security)
        secure_questions = []
        for q in exam_data['questions']:
            q_safe = q.copy()
            # Explicitly remove sensitive fields
            q_safe['correctAnswer'] = None
            q_safe['explanation'] = None
            # Ensure compatibility with QuestionV2
            q_safe['options'] = q.get('options', [])
            secure_questions.append(QuestionV2(**q_safe))

        return PracticeExamResponse(
            exam_id=exam_data['exam_id'],
            questions=secure_questions,
            total_marks=exam_data['total_marks'],
            duration_minutes=exam_data['duration']
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")