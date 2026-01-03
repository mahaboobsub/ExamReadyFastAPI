# 🚀 ExamReady RAG Pipeline - Complete Testing Guide

## 📋 Overview

Complete guide for testing the **RAG + LLM Exam Generation Pipeline**:
- **Full OCR Pipeline**: PyMuPDF + pix2text + Tesseract + Gemini Vision
- **All Subjects**: Mathematics, Physics, Chemistry, Biology (Class 10)
- **End-to-End**: PDF Download → Indexing → Qdrant → Exam Generation → PDF Export

---

## ✅ Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FULL OCR EXTRACTION PIPELINE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   NCERT PDFs ───┬──► PyMuPDF (Plain Text Extraction)               │
│                 │                                                   │
│                 ├──► pix2text (Formula/Equation → LaTeX)           │
│                 │                                                   │
│                 ├──► Tesseract OCR (Labeled Diagrams/Tables)       │
│                 │                                                   │
│                 └──► Gemini Vision (Pure Diagrams - optional)      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       QDRANT VECTOR STORE                           │
├─────────────────────────────────────────────────────────────────────┤
│  Collection: cbse_textbooks                                         │
│  Embeddings: Gemini text-embedding-004 (768 dims)                  │
│  Indexes: subject, chapter, class, board, content_type             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXAM GENERATION (RAG + LLM)                      │
├─────────────────────────────────────────────────────────────────────┤
│  1. Query Qdrant for chapter context (Hybrid Search)               │
│  2. Build prompt with RAG context                                  │
│  3. Gemini 2.5 Flash generates questions                           │
│  4. Organize into CBSE sections (A/B/C/D/E)                        │
│  5. Apply Bloom's taxonomy & difficulty distribution               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        PDF GENERATION                               │
├─────────────────────────────────────────────────────────────────────┤
│  Student Paper: exam_pdf.html (Questions only)                     │
│  Answer Key: answer_key_pdf.html (Solutions + Explanations)        │
│  Renderer: WeasyPrint                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Environment Setup

### Step 1: Clone and Install
```bash
cd c:\Users\Lenovo\Desktop\examready-fastapi

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install System Dependencies (for Full OCR)
```bash
# Tesseract OCR (Windows)
# Download: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
# Add to PATH

# Verify Tesseract
tesseract --version
```

### Step 3: Configure .env
```env
# API Keys
GEMINI_API_KEY=your_primary_gemini_key
GEMINI_API_KEY_2=optional_backup_key
GEMINI_API_KEY_3=optional_backup_key

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key

# Security
X_INTERNAL_KEY=dev_secret_key_12345

# Optional
REDIS_URL=redis://localhost:6379
```

---

## 📚 PHASE 1: Download PDFs

### Mathematics (Class 10)
```bash
# Create directory structure
mkdir -p data/textbooks/class_10/mathematics
mkdir -p data/pyq/class_10/mathematics
mkdir -p data/sample_papers/class_10/mathematics

# Download NCERT textbooks (14 chapters)
python scripts/download_ncert_maths.py

# Download Previous Year Questions
python scripts/download_pyqs.py

# Download Sample Papers
python scripts/download_sample_papers.py
```

**Expected Files:**
```
data/textbooks/class_10/mathematics/
├── jemh101.pdf  (Real Numbers)
├── jemh102.pdf  (Polynomials)
├── jemh103.pdf  (Linear Equations)
├── jemh104.pdf  (Quadratic Equations)
├── jemh105.pdf  (Arithmetic Progressions)
├── jemh106.pdf  (Triangles)
├── jemh107.pdf  (Coordinate Geometry)
├── jemh108.pdf  (Intro to Trigonometry)
├── jemh109.pdf  (Applications of Trigonometry)
├── jemh110.pdf  (Circles)
├── jemh111.pdf  (Areas Related to Circles)
├── jemh112.pdf  (Surface Areas and Volumes)
├── jemh113.pdf  (Statistics)
└── jemh114.pdf  (Probability)
```

**Manual Download (if script fails):**
- https://ncert.nic.in/textbook.php?jemh1=0-14

---

## 📚 PHASE 2: Download Other Subjects (For Future Testing)

### Physics (Class 10)
```bash
mkdir -p data/textbooks/class_10/physics

# Manual download from:
# https://ncert.nic.in/textbook.php?jeph1=0-16
# Save as: jeph101.pdf to jeph116.pdf
```

### Chemistry (Class 10)  
```bash
mkdir -p data/textbooks/class_10/chemistry

# Manual download from:
# https://ncert.nic.in/textbook.php?jesc1=0-16
# Save as: jesc101.pdf to jesc116.pdf
```

### Biology (Class 10)
```bash
mkdir -p data/textbooks/class_10/biology

# Manual download from:
# https://ncert.nic.in/textbook.php?jebo1=0-16
# Save as: jebo101.pdf to jebo116.pdf
```

---

## ⚙️ PHASE 3: Index into Qdrant (Full OCR Pipeline)

### Step 1: Create Qdrant Collection & Indexes
```bash
python scripts/index_textbooks.py
```

### Step 2: Index Mathematics with Full OCR
```bash
# This uses: PyMuPDF + pix2text + Tesseract + Gemini Vision
python scripts/reindex_all_textbooks_with_ocr.py
```

**What it does:**
1. Extracts plain text using PyMuPDF
2. Processes formulas/equations using pix2text → LaTeX
3. Extracts text from labeled diagrams using Tesseract OCR
4. Describes pure diagrams using Gemini Vision (if enabled)
5. Chunks text (1000 chars, 200 overlap)
6. Generates embeddings using Gemini text-embedding-004
7. Uploads to Qdrant with metadata

**Expected Output:**
```
📚 REINDEX ALL TEXTBOOKS WITH OCR ENHANCEMENT
   Using: PyMuPDF + pix2text + Tesseract + Gemini Vision
   
📖 Chapter 1: Real Numbers
   📄 Extracting text...
   🔍 Local OCR (formula) on p5
   📦 Generated 85 chunks with embeddings
   ☁️ Uploading to Qdrant...
   ✅ Uploaded 85 chunks
   
[... continues for all 14 chapters ...]

🎉 REINDEXING COMPLETE
   ✅ Processed: 14/14 chapters
   📦 Total chunks: 1500-2000
```

⏱️ **Time:** ~15-30 minutes (depending on Vision usage)

### Step 3: Verify Qdrant Coverage
```bash
python scripts/check_qdrant_coverage.py
```

**Expected:**
```
CHAPTER COVERAGE ANALYSIS
Chapter                                 Chunks    Status
Real Numbers                           85        GOOD ✅
Polynomials                            92        GOOD ✅
...
Total: 14/14 chapters with data (1521 chunks)
```

---

## ⚙️ PHASE 4: Index Other Subjects (Same Pipeline)

### For Physics
```python
# scripts/process_physics_textbook.py (create by copying maths version)

TEXTBOOK_DIR = "data/textbooks/class_10/physics"
TEXTBOOK_FILES = [
    ("jeph101.pdf", 1, "Light - Reflection and Refraction"),
    ("jeph102.pdf", 2, "The Human Eye and the Colourful World"),
    # ... add all chapter mappings
]

# Change metadata:
metadata = {
    "subject": "Physics",  # Changed
    "chapter": chapter_name,
    # ... rest same
}
```

### For Chemistry
```python
# scripts/process_chemistry_textbook.py

TEXTBOOK_DIR = "data/textbooks/class_10/chemistry"
# Similar changes as above
metadata = {"subject": "Chemistry", ...}
```

### For Biology
```python
# scripts/process_biology_textbook.py

TEXTBOOK_DIR = "data/textbooks/class_10/biology"
metadata = {"subject": "Biology", ...}
```

**Key Point:** The same OCR pipeline (`IndexingService`) works for ALL subjects!
Only changes needed:
1. Chapter mapping (PDF filenames → chapter names)
2. Subject name in metadata
3. Directory path

---

## 🚀 PHASE 5: Start Server

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Expected:**
```
INFO:     Started server process
✅ Connected to Qdrant Cloud
🔑 Loaded 1 Gemini API keys for rotation
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001
```

---

## 🧪 PHASE 6: Generate Exams

### Option A: Via API (Recommended)
```bash
curl -X POST "http://127.0.0.1:8001/v1/exam/generate-board" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: dev_secret_key_12345" \
  -d '{
    "board": "CBSE",
    "class_num": 10,
    "subject": "Mathematics",
    "chapters": [
      "Real Numbers",
      "Polynomials", 
      "Quadratic Equations",
      "Statistics",
      "Probability"
    ]
  }'
```

### Option B: Full 14-Chapter Exam Script
```bash
python scripts/generate_full_14_chapter_exam.py
```

### Option C: End-to-End Pipeline Test
```bash
python scripts/test_pipeline.py
```

**Expected Output:**
```
🧪 EXAM GENERATION PIPELINE TEST
STEP 1: API Health Check ✅
STEP 2: Exam Generation (5 chapters)
   Generation time: 296.5 seconds
   Total Questions: 38
   Total Marks: 80 ✅
STEP 3: JSON Validation ✅
STEP 4: Student PDF Generation ✅
STEP 5: Answer Key PDF Generation ✅

Overall: 5/5 tests passed 🎉
```

---

## 📄 PHASE 7: Export PDFs

### Generate PDFs from JSON
```bash
python -c "
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import json

with open('pipeline_test_exam_OFFICIAL.json', 'r', encoding='utf-8') as f:
    exam = json.load(f)

env = Environment(loader=FileSystemLoader('app/templates'))

# Student Paper
template = env.get_template('exam_pdf.html')
html = template.render(exam=exam)
HTML(string=html).write_pdf('Student_Exam.pdf')

# Answer Key
template = env.get_template('answer_key_pdf.html')
html = template.render(exam=exam)
HTML(string=html).write_pdf('Answer_Key.pdf')

print('PDFs generated!')
"
```

---

## ✅ PHASE 8: Validate Quality

```bash
# Validate exam structure and quality
python scripts/validate_exam_quality.py pipeline_test_exam_OFFICIAL.json

# Analyze exam metrics
python scripts/analyze_exam.py
```

**Expected Quality Score:** 85-95/100

---

## 📊 Same Code for All Subjects?

### ✅ YES - Same Pipeline Works!

| Component | Maths | Physics | Chemistry | Biology |
|-----------|-------|---------|-----------|---------|
| PDF Extraction (PyMuPDF) | ✅ | ✅ | ✅ | ✅ |
| Formula OCR (pix2text) | ✅ | ✅ | ✅ | ⚠️ Less formulas |
| Diagram OCR (Tesseract) | ✅ | ✅ | ✅ | ✅ |
| Vision (Gemini) | ✅ | ✅ | ✅ | ✅ |
| Embeddings (Gemini) | ✅ | ✅ | ✅ | ✅ |
| Qdrant Storage | ✅ | ✅ | ✅ | ✅ |
| Exam Generation API | ✅ | ✅ | ✅ | ✅ |
| PDF Export | ✅ | ✅ | ✅ | ✅ |

---

## 🔧 Subject-Specific Customization Guide

### Files That Need Changes Per Subject

| File | What to Change | Priority |
|------|----------------|----------|
| `scripts/process_<subject>_textbook.py` | Chapter mapping | **REQUIRED** |
| `app/config/cbse_templates.py` | Add subject template | REQUIRED |
| `app/services/llm_exam_generator.py` | System prompt (optional) | Optional |
| `app/config/prompts.py` | Subject-specific prompts | Optional |

---

### STEP 1: Create Indexing Script for New Subject

**Copy from:** `scripts/reindex_all_textbooks_with_ocr.py`

**Create:** `scripts/reindex_physics_textbooks.py`

```python
# Change these lines:

# Line 17: Directory path
TEXTBOOK_DIR = "data/textbooks/class_10/physics"  # Changed

# Lines 19-34: Chapter mapping
TEXTBOOK_FILES = [
    ("jeph101.pdf", 1, "Light - Reflection and Refraction"),
    ("jeph102.pdf", 2, "Human Eye and Colourful World"),
    ("jeph103.pdf", 3, "Electricity"),
    ("jeph104.pdf", 4, "Magnetic Effects of Electric Current"),
    ("jeph105.pdf", 5, "Sources of Energy"),
    # Add all chapters...
]

# Lines 71-79: Metadata
metadata = {
    "board": "CBSE",
    "class": 10,
    "class_num": 10,
    "subject": "Physics",  # ⭐ CHANGED
    "chapter": chapter_name,
    "chapter_id": chapter_id,
    "textbook": "NCERT Physics Class 10",  # ⭐ CHANGED
    "processed_with_ocr": True
}
```

---

### STEP 2: Add Template in `app/config/cbse_templates.py`

**Add after line 72:**

```python
# Physics Template
CBSE_10_PHYSICS_BOARD_2025 = CBSETemplate(
    pattern_id="CBSE_10_PHYSICS_BOARD_2025",
    board="CBSE",
    class_num=10,
    subject="Physics",
    pattern_type="board_exam",
    total_marks=80,
    duration_minutes=180,
    sections=[
        {"code": "A", "name": "Section A - Objective", "question_count": 20, "marks_per_question": 1, "question_type": "MCQ"},
        {"code": "B", "name": "Section B - VSA", "question_count": 5, "marks_per_question": 2, "question_type": "VSA"},
        {"code": "C", "name": "Section C - SA", "question_count": 6, "marks_per_question": 3, "question_type": "SA"},
        {"code": "D", "name": "Section D - LA", "question_count": 4, "marks_per_question": 5, "question_type": "LA"},
        {"code": "E", "name": "Section E - Case-Based", "question_count": 3, "marks_per_question": 4, "question_type": "CASE_BASED"}
    ],
    overall_blooms={"Remember": 20, "Understand": 25, "Apply": 30, "Analyze": 20, "Evaluate": 5},
    applicable_chapters=[
        "Light - Reflection and Refraction",
        "Human Eye and Colourful World", 
        "Electricity",
        "Magnetic Effects of Electric Current",
        "Sources of Energy"
    ],
    chapter_weightage={
        "Light - Reflection and Refraction": 10,
        "Human Eye and Colourful World": 8,
        "Electricity": 15,
        "Magnetic Effects of Electric Current": 12,
        "Sources of Energy": 5
    }
)

# Chemistry Template
CBSE_10_CHEMISTRY_BOARD_2025 = CBSETemplate(
    pattern_id="CBSE_10_CHEMISTRY_BOARD_2025",
    board="CBSE",
    class_num=10,
    subject="Chemistry",
    pattern_type="board_exam",
    total_marks=80,
    duration_minutes=180,
    sections=[
        {"code": "A", "name": "Section A - Objective", "question_count": 20, "marks_per_question": 1, "question_type": "MCQ"},
        {"code": "B", "name": "Section B - VSA", "question_count": 5, "marks_per_question": 2, "question_type": "VSA"},
        {"code": "C", "name": "Section C - SA", "question_count": 6, "marks_per_question": 3, "question_type": "SA"},
        {"code": "D", "name": "Section D - LA", "question_count": 4, "marks_per_question": 5, "question_type": "LA"},
        {"code": "E", "name": "Section E - Case-Based", "question_count": 3, "marks_per_question": 4, "question_type": "CASE_BASED"}
    ],
    overall_blooms={"Remember": 20, "Understand": 25, "Apply": 30, "Analyze": 20, "Evaluate": 5},
    applicable_chapters=[
        "Chemical Reactions and Equations",
        "Acids, Bases and Salts",
        "Metals and Non-Metals",
        "Carbon and its Compounds",
        "Periodic Classification of Elements"
    ]
)

# Biology Template
CBSE_10_BIOLOGY_BOARD_2025 = CBSETemplate(
    pattern_id="CBSE_10_BIOLOGY_BOARD_2025",
    board="CBSE",
    class_num=10,
    subject="Biology",
    pattern_type="board_exam",
    total_marks=80,
    duration_minutes=180,
    sections=[
        {"code": "A", "name": "Section A - Objective", "question_count": 20, "marks_per_question": 1, "question_type": "MCQ"},
        {"code": "B", "name": "Section B - VSA", "question_count": 5, "marks_per_question": 2, "question_type": "VSA"},
        {"code": "C", "name": "Section C - SA", "question_count": 6, "marks_per_question": 3, "question_type": "SA"},
        {"code": "D", "name": "Section D - LA", "question_count": 4, "marks_per_question": 5, "question_type": "LA"},
        {"code": "E", "name": "Section E - Case-Based", "question_count": 3, "marks_per_question": 4, "question_type": "CASE_BASED"}
    ],
    overall_blooms={"Remember": 25, "Understand": 30, "Apply": 25, "Analyze": 15, "Evaluate": 5},
    applicable_chapters=[
        "Life Processes",
        "Control and Coordination",
        "How do Organisms Reproduce",
        "Heredity and Evolution",
        "Our Environment",
        "Management of Natural Resources"
    ]
)

# Add to TEMPLATES registry (around line 95)
TEMPLATES = {
    "CBSE_10_SCIENCE_BOARD_2025": CBSE_10_SCIENCE_BOARD_2025,
    "CBSE_10_MATHS_BOARD_2025": CBSE_10_MATHS_BOARD_2025,
    "CBSE_10_PHYSICS_BOARD_2025": CBSE_10_PHYSICS_BOARD_2025,    # Add
    "CBSE_10_CHEMISTRY_BOARD_2025": CBSE_10_CHEMISTRY_BOARD_2025,  # Add
    "CBSE_10_BIOLOGY_BOARD_2025": CBSE_10_BIOLOGY_BOARD_2025       # Add
}
```

---

### STEP 3: Update System Prompt (Optional but Recommended)

**File:** `app/services/llm_exam_generator.py`

**Location:** Lines 18-50 (system_prompt)

**For Physics:**
```python
self.system_prompt = """
You are an expert CBSE Physics question paper setter for Class 10.

### ROLE & RESPONSIBILITIES
- Generate questions strictly from NCERT Class 10 Physics curriculum
- Focus on: Light, Electricity, Magnetism, Energy topics
- Include numerical problems with proper SI units
- Create diagram-based questions where appropriate

### OUTPUT FORMAT (same JSON structure)
...
"""
```

**For Chemistry:**
```python
self.system_prompt = """
You are an expert CBSE Chemistry question paper setter for Class 10.

### ROLE & RESPONSIBILITIES
- Generate questions from NCERT Class 10 Chemistry curriculum
- Include balanced chemical equations where appropriate
- Focus on: Reactions, Acids/Bases, Metals, Carbon compounds
- Use proper chemical nomenclature and symbols

### OUTPUT FORMAT (same JSON structure)
...
"""
```

**For Biology:**
```python
self.system_prompt = """
You are an expert CBSE Biology question paper setter for Class 10.

### ROLE & RESPONSIBILITIES
- Generate questions from NCERT Class 10 Biology curriculum
- Include diagram-based questions (human systems, processes)
- Focus on: Life Processes, Reproduction, Heredity, Environment
- Use proper biological terminology

### OUTPUT FORMAT (same JSON structure)
...
"""
```

---

### STEP 4: Generate Exam for New Subject

**Via API:**
```bash
curl -X POST "http://127.0.0.1:8001/v1/exam/generate-board" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: dev_secret_key_12345" \
  -d '{
    "board": "CBSE",
    "class_num": 10,
    "subject": "Physics",
    "chapters": [
      "Light - Reflection and Refraction",
      "Electricity",
      "Magnetic Effects of Electric Current"
    ]
  }'
```

---

## 📂 Complete File Reference

### App Directory Structure (All Files Verified ✅)

```
app/
├── config/
│   ├── __init__.py
│   ├── settings.py           # API keys, Qdrant config
│   ├── prompts.py            # LLM prompts for all features
│   └── cbse_templates.py     # ⭐ Add subject templates here
│
├── middleware/
│   └── logging_middleware.py # Request logging
│
├── models/
│   ├── exammodels.py         # Exam request/response models
│   └── ...
│
├── routers/
│   ├── exam.py               # /v1/exam/* endpoints
│   └── ...
│
├── services/
│   ├── geminiservice.py      # Gemini API (text generation + embeddings)
│   ├── qdrant_service.py     # Vector DB operations
│   ├── llm_exam_generator.py # ⭐ Update system_prompt for subjects
│   ├── indexingservice.py    # OCR pipeline orchestrator
│   ├── visionservice.py      # Gemini Vision for diagrams
│   ├── pdfgenerator.py       # PDF export
│   └── pdf_processor/
│       ├── pdf_extractor.py  # PyMuPDF + pix2text + Tesseract
│       ├── hindi_remover.py  # Bilingual PDF handling
│       ├── solution_detector.py # Answer/solution detection
│       └── pyq_processor.py  # PYQ processing
│
├── templates/
│   ├── exam_pdf.html         # Student paper template
│   └── answer_key_pdf.html   # Answer key template
│
├── utils/
│   └── pdfextractor.py       # Utility PDF extractor
│
└── main.py                   # FastAPI entry point
```

### Scripts Directory (Essential Only)

```
scripts/
├── download_ncert_maths.py        # Download mathematics PDFs
├── download_pyqs.py               # Download previous year papers
├── download_sample_papers.py      # Download sample papers
├── download_chemistry_units.py    # Future: Chemistry downloads
│
├── reindex_all_textbooks_with_ocr.py  # ⭐ FULL OCR indexing (use this!)
├── index_textbooks.py             # Create Qdrant indexes
│
├── check_qdrant_coverage.py       # Verify data coverage
├── test_pipeline.py               # End-to-end test
├── validate_exam_quality.py       # Quality validation
├── analyze_exam.py                # Exam structure analysis
├── generate_full_14_chapter_exam.py # Full exam generation
│
├── apply_official_cbse_pattern.py # CBSE pattern fix
├── fix_exam_metadata.py           # Metadata fixes
├── backup_qdrant_collection.py    # Backup data
└── clear_textbook_collection.py   # Clear collection
```

---

## 🧹 Essential Files Only (Cleanup)

### ✅ KEEP - Core Application (DO NOT DELETE)
```
app/
├── config/           # Settings, prompts, templates
├── middleware/       # Logging
├── models/          # Pydantic models
├── routers/         # API endpoints
├── services/        # Business logic
│   ├── geminiservice.py         # LLM API
│   ├── qdrant_service.py        # Vector DB
│   ├── llm_exam_generator.py    # Exam generation
│   ├── indexingservice.py       # OCR pipeline orchestrator
│   ├── visionservice.py         # Gemini Vision
│   ├── pdf_processor/           # Full OCR pipeline
│   │   ├── pdf_extractor.py     # PyMuPDF + pix2text + Tesseract
│   │   └── ...
│   └── ...
├── templates/       # PDF templates
├── utils/           # Utilities
└── main.py          # FastAPI entry
```

### ✅ KEEP - Essential Scripts
```
scripts/
├── download_ncert_maths.py           # Download textbooks
├── download_pyqs.py                  # Download PYQs
├── download_sample_papers.py         # Download samples
├── reindex_all_textbooks_with_ocr.py # FULL OCR indexing ⭐
├── index_textbooks.py                # Create Qdrant indexes
├── check_qdrant_coverage.py           # Verify data
├── test_pipeline.py                  # E2E test
├── validate_exam_quality.py          # Quality validation
├── analyze_exam.py                   # Structure analysis
├── generate_full_14_chapter_exam.py  # Full exam generation
├── apply_official_cbse_pattern.py    # CBSE pattern fix
├── fix_exam_metadata.py              # Metadata fixes
├── backup_qdrant_collection.py       # Backup data
└── clear_textbook_collection.py      # Clear collection
```

### ❌ DELETE - Not Needed
```
# Root directory temp files
backup_textbooks_*.json
board_gen_debug.log
code*.txt
debug_*.png
exam_*.txt, exam_*.json
full_*.json (all versions)
latest_*.json
pipeline_*.json, pipeline_*.pdf
qdrant_*.json
CBSE_*.pdf

# Debug scripts (40+ files)
scripts/debug_*.py
scripts/check_*.py (except check_qdrant_coverage.py)
scripts/test_*.py  (except test_pipeline.py)
scripts/validate_v*.py
scripts/verify_*.py
scripts/quick_*.py
scripts/final_*.py
scripts/fix_*.py (except fix_exam_metadata.py)
scripts/process_maths_textbook.py  # Use _v2 or reindex_all instead
scripts/process_maths_textbook_v2.py  # Superseded by reindex_all

# Folders
validation_results/
.pytest_cache/
__pycache__/ (all)
.data/
```

---

## 🔥 Quick Test Checklist

```
[ ] Environment setup complete (.env configured)
[ ] Tesseract installed and in PATH
[ ] NCERT PDFs downloaded (14 chapters)
[ ] `python scripts/reindex_all_textbooks_with_ocr.py` completed
[ ] `python scripts/check_qdrant_coverage.py` shows 14/14 chapters
[ ] Server starts without errors
[ ] `python scripts/test_pipeline.py` passes 5/5 tests
[ ] Generated exam has 38 questions, 80 marks
[ ] PDF files are > 50 KB
[ ] Quality score > 85/100
```

---

## ⚠️ Common Issues

### Issue 1: Tesseract Not Found
```
Error: TesseractNotFoundError
Fix: Install Tesseract and add to PATH
     https://github.com/UB-Mannheim/tesseract/wiki
```

### Issue 2: pix2text Model Loading Failed
```
Error: Failed to load pix2text model
Fix: pip install pix2text --upgrade
     Or: Set use_ocr=False to skip formula OCR
```

### Issue 3: Gemini Rate Limit (429)
```
Fix: Add backup keys to .env (GEMINI_API_KEY_2, etc.)
     Or: Wait 60 seconds and retry
```

### Issue 4: Empty Qdrant Results
```
Fix: python scripts/check_qdrant_coverage.py
     If 0 chunks: Re-run indexing script
```

---

## 📞 Summary

| Step | Command | Time |
|------|---------|------|
| 1. Setup | `pip install -r requirements.txt` | 2 min |
| 2. Download PDFs | `python scripts/download_ncert_maths.py` | 5 min |
| 3. Index (Full OCR) | `python scripts/reindex_all_textbooks_with_ocr.py` | 15-30 min |
| 4. Verify | `python scripts/check_qdrant_coverage.py` | 1 min |
| 5. Start Server | `python -m uvicorn app.main:app --port 8001` | 30 sec |
| 6. Test | `python scripts/test_pipeline.py` | 5 min |
| 7. Generate Exam | `python scripts/generate_full_14_chapter_exam.py` | 5-8 min |

**Total Time:** ~30-45 minutes (first run)

---

## 🎉 Success Criteria

Your testing is complete when:
- ✅ All 14 chapters indexed in Qdrant
- ✅ Pipeline test passes 5/5
- ✅ Generated exam: 38 questions, 80 marks
- ✅ Quality score: > 85/100
- ✅ PDFs render correctly (> 50 KB each)
- ✅ All subjects can use same pipeline (just change chapter mapping)

Good luck! 🚀
