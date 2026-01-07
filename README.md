# 📚 ExamReady FastAPI - AI-Powered Education Platform

**Status:** Production Ready (Phase 3 Complete)  
**Version:** 3.0.0

---

## 🎯 Project Overview

**ExamReady FastAPI** is an advanced AI-driven backend for educational platforms, designed to generate **CBSE Board Exams**, **Quizzes**, **Flashcards**, and provide **AI Tutoring**. 

It leverages a state-of-the-art **RAG (Retrieval-Augmented Generation)** pipeline using **Qdrant** (Vector DB), **Google Gemini 2.5 Flash** (LLM), and a sophisticated **OCR stack** (Tesseract + Pix2Text + Gemini Vision) to ingest textbooks and generate high-quality, curriculum-aligned content.

---

## 🌟 Key Features

### 1. 📝 Intelligent Exam Generation
- **Board Exams:** Generates full 38-question Class 10 Maths exams adhering to strict CBSE blueprints (Section A-E).
- **Custom Exams:** Allows teachers to create exams for specific chapters and difficulty levels.
- **Output:** Produces valid JSON metadata and professionally formatted PDFs with LaTeX math rendering.

### 2. 🧠 AI Tutor (RAG-Powered)
- **Context-Aware:** Answers student queries by retrieving relevant textbook chunks.
- **Dual-Collection Strategy:** Uses separate vector indexes for general knowledge (textbooks) and specific question retrieval (question bank).

### 3. ⚡ Quizzes & Flashcards
- **Instant Generation:** Converts chapter content into interactive quizzes and study flashcards.
- **Adaptive:** Supports varying difficulty levels (Easy, Medium, Hard).

### 4. 🖼️ Advanced OCR Pipeline
- **Multi-Modal:** Extracts text, math formulas, and diagrams from PDFs.
- **Stack:** PyMuPDF (Layout) + Tesseract (Text) + Pix2Text (Math) + Gemini Vision (Complex Analysis).

---

## 🏗️ Architecture & Services

The project follows a modular micro-services architecture under `app/services/`:

| Service | Description |
|---------|-------------|
| **`llm_exam_generator.py`** | Orchestrates full exam generation logic. |
| **`board_exam_generator.py`** | Specialized logic for CBSE board simulation. |
| **`qdrant_service.py`** | Manages Vector DB interactions (Search, Upsert). |
| **`geminiservice.py`** | Wrapper for Google Gemini API with key rotation. |
| **`pdfgenerator.py`** | Converts Exam HTML/JSON to PDF using WeasyPrint. |
| **`indexingservice.py`** | Handles text chunking and embedding generation. |
| **`quality_scorer.py`** | Automates exam validation (0-100 score). |

---

## 🛠️ RAG Pipeline & Data Ingestion

We rely on a **Dual-Collection Strategy** to serve different use cases:

### Collection 1: `cbse_textbooks` (For AI Tutor)
- **Content:** Smartly chunked paragraphs from NCERT textbooks.
- **Purpose:** Answering "Explain Pythagoras theorem" type questions.
- **Pipeline:** `scripts/master_upload.py` scans raw PDFs, applies OCR, chunks text, and uploads to Qdrant.

### Collection 2: `cbse_questions_v2` (For Exam Rules)
- **Content:** 500+ individual questions tagged with metadata.
- **Metadata:** `chapter`, `question_type` (MCQ, VSA, SA, LA), `marks`, `difficulty`, `blooms_level`.
- **Purpose:** Enforcing rules like "Q19 must be Assertion-Reason from Triangles".
- **Pipeline:** `scripts/extract_questions_from_pdfs.py` -> `scripts/classify_questions.py` -> `scripts/upload_questions_to_qdrant.py`.

---

## 📂 Repository Structure

```
examready-fastapi/
├── app/
│   ├── main.py                   # FastAPI Application Entrypoint
│   ├── config/                   # Settings (.env) & Prompts
│   ├── routers/                  # API Endpoints (exam, quiz, tutor)
│   ├── services/                 # Core Business Logic (LLM, RAG, PDF)
│   ├── models/                   # Pydantic Schemas
│   └── templates/                # HTML Templates for PDF Generation
├── data/                         # Data Storage
│   ├── raw/                      # Raw PDFs (Textbooks, PYQs)
│   ├── processed/                # Extracted JSONs
│   └── pdfs/                     # Generated Exam PDFs
├── scripts/                      # Automation Scripts
│   ├── master_upload.py          # Pipeline A: Textbook Ingestion
│   ├── extract_questions_*.py    # Pipeline B: Question Extraction
│   ├── generate_exam_00*.py      # Exam Generation (005=Prod, 007=Hard)
│   └── package_exams.py          # Bundle exams for review
├── tests/                        # Pytest Suite
└── requirements.txt              # Dependency List
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Tesseract OCR installed on system
- Qdrant Cloud Cluster (or local Docker)
- Google Gemini API Key

### 2. Setup Environment
Clone repo and setup `.env`:
```bash
cp .env.example .env
```
**Required Variables:**
```env
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION_NAME=cbse_textbooks
```

### 3. Install Dependencies
```bash
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Server
```bash
uvicorn app.main:app --reload
```
API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Routine Scripts

### Data Pipeline
```bash
# Upload Textbooks (Phase A)
python scripts/master_upload.py

# Setup Question Bank (Phase B)
python scripts/setup_question_collection.py
python scripts/extract_questions_from_pdfs.py
python scripts/classify_questions.py
python scripts/upload_questions_to_qdrant.py
```

### Exam Generation
```bash
# Generate Production Exam (Exam 005)
python scripts/finalize_exam_005.py

# Generate Hard Exam (Exam 007)
python scripts/generate_exam_007.py
```

### Validation
```bash
python scripts/validate_exam_quality.py test_output/exam_test_005.json
```

---

## 📊 Quality Metrics

We strictly validate every generated exam:
- **Bloom's Taxonomy:** Ensuring mix of Remember (20%), Understand (30%), Apply (30%), Analyze (20%).
- **Difficulty:** Easy (30%), Medium (50%), Hard (20%).
- **Uniqueness:** Exams are checked against previous versions to prevent duplicates.

**Current Production Standard (Exam 005):**
- **Score:** 95/100
- **Status:** Gold Standard

---

## 🤝 Contributing

1. **Pull Latest:** `git pull origin feature/fastapi-ai-service`
2. **Review Guides:**
   - [Team Testing Guide](TEAM_TESTING_GUIDE.md)
   - [Cleanup Guide](CLEANUP_GUIDE.md)
   - [Dual Collection Roadmap](DUAL_COLLECTION_ROADMAP.md)
3. **Commit:** Ensure pre-commit checks pass.

---

**© 2026 ExamReady AI Team**
