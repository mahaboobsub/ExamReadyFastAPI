# 🗂️ Essential Files Guide - ExamReady FastAPI

This guide lists the **critical files** required to run, test, and contribute to the ExamReady system. Use this to orient new team members or verify your own environment.

---

## 🚀 1. Data Ingestion & RAG Pipeline
**Goal:** Ingest PDFs, extract content with OCR, and store in Qdrant.

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Pipeline Driver** | `scripts/master_upload.py` | **Start Here.** Main script to process PDFs using the OCR stack and upload to `cbse_textbooks`. |
| **OCR Stack** | `app/utils/pdfextractor.py` | Contains the **PyMuPDF + Tesseract + Pix2Text** logic. This is the "brain" of extraction. |
| **Indexing Logic** | `app/services/indexingservice.py` | Handles chunking, embedding generation (Gemini), and preparation for Qdrant. |
| **Vector DB** | `app/services/qdrant_service.py` | Manages connection to Qdrant Cloud. Handles searches and upserts. |

**✅ How to Test RAG:**
```bash
python scripts/master_upload.py  # Run full ingestion
python scripts/check_qdrant_coverage.py  # Verify data exists
```

---

## 📝 2. Exam Generation Engine
**Goal:** Create valid CBSE Class 10 Board Exams.

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Production Script** | `scripts/finalize_exam_005.py` | **Run This.** Generates a production-ready exam with the current best settings. |
| **Orchestrator** | `app/services/llm_exam_generator.py` | High-level logic that coordinates Qdrant retrieval and Gemini generation. |
| **Board Logic** | `app/services/board_exam_generator.py` | Specific rules for CBSE (38 Qs, Sections A-E, Blueprints). |
| **PDF Export** | `app/services/pdfgenerator.py` | Converts the generated exam JSON into a PDF using WeasyPrint + LaTeX. |

**✅ How to Test Exams:**
```bash
python scripts/finalize_exam_005.py  # Verify it runs to completion
python scripts/validate_exam_quality.py test_output/exam_test_005.json # Check score
```

---

## 🎓 3. AI Tutor & Education Features
**Goal:** Interactive tutoring and study aids.

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Tutor API** | `app/routers/tutor.py` | Endpoint `/v1/tutor/answer`. Connects student queries -> `qdrant_service` -> Gemini. |
| **Quiz API** | `app/routers/quiz.py` | Endpoint `/v1/quiz/generate`. Creates MCQs from specific chapters. |
| **Flashcards API** | `app/routers/flashcards.py` | Endpoint `/v1/flashcards`. Generates key-term flashcards. |

**✅ How to Test Tutor:**
`tests/test_rag_accuracy.py` verifies that the retrieval system finds the right textbook chunks for a given query.

---

## 🧩 4. Dual-Collection Strategy (Phase B)
**Goal:** Advanced rule-based retrieval for exam generation.

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Extractor** | `scripts/extract_questions_from_pdfs.py` | Extracts individual Q&A pairs from PDFs page-by-page. |
| **Classifier** | `scripts/classify_questions.py` | Tags questions with Metadata (Easy/Medium/Hard, Bloom's Level). |
| **Uploader** | `scripts/upload_questions_to_qdrant.py` | Uploads strictly classified questions to `cbse_questions_v2`. |

---

## ✅ 5. Verification & Tests
**Goal:** Verify system health before pushing code.

| Type | File Path | Use Case |
|------|-----------|----------|
| **RAG Test** | `tests/test_rag_accuracy.py` | **CRITICAL.** Checks if Qdrant is returning relevant context. |
| **Exam Logic** | `tests/test_exam_logic.py` | Verifies question counts, marks distribution, and sections. |
| **Full Suite** | `tests/run_all.py` | Runs all relevant tests in one go. |
| **Inventory** | `scripts/verify_pdf_inventory.py` | Checks if required raw PDFs are present in `data/raw`. |

---

## 🛠️ Summary for New Teammates

**To start working on:**
1.  **RAG/Ingestion:** Focus on `scripts/master_upload.py` and `app/utils/pdfextractor.py`.
2.  **Exam Logic:** Focus on `app/services/board_exam_generator.py` and `scripts/finalize_exam_005.py`.
3.  **Frontend/API:** Focus on `app/routers/` files.

**Essential Download List:**
- Raw PDFs in `data/raw/cbse_class10_pdfs/maths/`
- `.env` file (ask lead for keys)
