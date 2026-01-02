# examready-fastapi

Overview
--------
examready-fastapi is a FastAPI-based backend that powers exam, quiz, flashcard, and tutor endpoints. It includes services for retrieval (BM25, Chroma), generative/model-backed helpers, PDF extraction and generation, and vision/OCR utilities used to build educational study content and assessments.

Features
--------
- FastAPI app with modular routers for exams, quizzes, flashcards, and tutor flows.
- Retrieval services: BM25 and vector store (Chroma) integration.
- RAG support with reranking and re-ranking helpers.
- PDF extraction and PDF generation utilities used to convert exam/textbook content.
- Vision/OCR helpers for image-based question processing.
- Scripts to index, test, and verify extraction and RAG behavior.

Quick start
-----------

### 1. Clone & enter the project
- `git clone <YOUR_REPO_URL>.git`
- `cd examready-fastapi`

### 2. Create and activate a virtualenv
- **Windows (PowerShell)**  
  - `python -m venv venv`  
  - `venv\Scripts\Activate.ps1`
- **macOS/Linux**  
  - `python3 -m venv venv`  
  - `source venv/bin/activate`

### 3. Install dependencies
- `pip install -r requirements.txt`

### 4. Configure environment variables
- Create a `.env` file in the project root (or copy from `.env.example` if you add one) and set at least:
  - `GEMINI_API_KEY=<your-google-gemini-key>`
  - `GEMINI_MODEL=gemini-2.5-flash` (or similar)
  - `REDIS_URL=<your-redis-or-upstash-url>`
  - `CHROMA_PATH=./data/chromadb`
  - `X_INTERNAL_KEY=dev_secret_key_12345`  (used in tests and sample clients)

### 5. Start the API server
- From the project root (with venv active):  
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Open interactive docs at: `http://localhost:8000/docs`

Repository structure
-------------------
- `app/` : main application code
  - `main.py` — FastAPI application entrypoint.
  - `config/` — configuration and prompt settings (`prompts.py`, `settings.py`).
  - `middleware/` — request logging and middleware helpers.
  - `models/` — Pydantic models for exams, flashcards, quizzes, and tutor flows.
  - `routers/` — API route definitions: `exam.py`, `flashcards.py`, `quiz.py`, `tutor.py`.
  - `services/` — core services including `bm25service.py`, `chromaservice.py`, `geminiservice.py`, `indexingservice.py`, `pdfgenerator.py`, `ragservice.py`, `rerankerservice.py`, `visionservice.py`.
  - `utils/` — utilities such as `cache.py` and `pdfextractor.py`.

- `data/` : runtime and indexed data
  - `bm25/` — BM25 indexes
  - `chromadb/` — Chroma DB files (example: `chroma.sqlite3` and a collection folder)
  - `pdfs/exams/` — extracted or stored exam HTML files
  - `textbooks/` — source textbook PDFs or extracted content (organized by board)

- `scripts/` : convenience and maintenance scripts
  - `download_pdfs.py`, `index_all.py`, `final_audit.py`, and various test/verification scripts such as `test_extraction.py`, `test_rag.py`, and `visual_verification.py`.

- `tests/` : automated tests
  - Unit and integration tests covering exam logic, APIs, RAG accuracy, flashcards, tutors, and more (e.g. `test_exam_logic.py`, `test_quiz_api.py`, `test_rag_accuracy.py`).

- Root files
  - `requirements.txt` — Python dependencies
  - `Dockerfile` — optional container build
  - `files_md.sh`, `code.txt` — helper files and notes

RAG pipeline
------------
The repository includes a Retrieval-Augmented Generation (RAG) pipeline used to answer user questions with grounding from indexed documents. A typical pipeline flow:

- Extraction & preprocessing: source PDFs and HTML (in `data/pdfs`) are parsed by `app/utils/pdfextractor.py` and other extractors to produce plain text and metadata.
- Chunking & embeddings: extracted text is chunked and embedded (via the embedding/LLM service in `app/services`, e.g. `geminiservice.py`) to produce dense vectors.
- Indexing: vectors are stored in a vector store (Chroma under `data/chromadb/`) and optionally BM25 indexes are created under `data/bm25/`.
- Retrieval: on a query, the system retrieves top-k candidates from Chroma (and/or BM25) using `app/services/chromaservice.py` and `app/services/bm25service.py`.
- Reranking: `app/services/rerankerservice.py` can rerank retrieved passages for better relevance.
- Prompt assembly: selected passages and metadata are assembled into a prompt using templates in `app/config/prompts.py`.
- Generation: the assembled prompt is sent to the generative model via `app/services/ragservice.py` or `app/services/geminiservice.py` to produce a final, citation-aware answer.
- Post-processing: answers are formatted, any citations or source links are attached, and results may be cached (`app/utils/cache.py`) or logged.

This modular flow allows swapping components (e.g., different vector stores, rerankers, or LLMs) and tuning retrieval / re-ranking strategies.

API endpoints (features)
------------------------
The API surface is organized under `app/routers/`. Key feature endpoints include:

- Exams (`app/routers/exam.py`): create, list, retrieve, and generate exam-related content and HTML exports (used for importing/exporting exam files under `data/pdfs/exams`). Typical operations: `GET /exams`, `POST /exams`, `GET /exams/{id}` and generation endpoints.
- Quizzes (`app/routers/quiz.py`): generate quizzes from source material, score or evaluate quiz attempts, and retrieve quiz metadata. Typical operations: `POST /quiz/generate`, `GET /quiz/{id}`.
- Flashcards (`app/routers/flashcards.py`): create and fetch flashcard sets derived from chapters or selected text. Typical operations: `POST /flashcards/generate`, `GET /flashcards/{id}`.
- Tutor (`app/routers/tutor.py`): interactive tutoring endpoints that accept user questions, run the RAG pipeline, and return step-by-step explanations or hints. Typical operations: `POST /tutor/session` or `POST /tutor/chat` to continue a tutoring session.

Other service endpoints and utilities:

- Indexing and maintenance scripts: `scripts/index_all.py` and related scripts provide CLI-style indexing and audit flows for keeping vector stores and BM25 indexes up to date.
- Vision/OCR helpers: `app/services/visionservice.py` and tests in `scripts/test_ocr.py` / `scripts/test_vision.py` show how image-based questions are processed and integrated into the pipeline.
- PDF generation: `app/services/pdfgenerator.py` exposes helpers to build printable/exportable exam documents.

Notes & next steps
------------------
- This README is a concise summary derived from the repository layout. If you want, I can:
  - Add example API usage and sample requests.
  - Add environment and setup instructions (virtualenv, env vars).
  - Expand service docs (how to run indexing, run RAG workflows).






| Old System             | New System                     |
| ---------------------- | ------------------------------ |
| HybridRAGService()     | qdrant_service (singleton)     |
| rag_service.search()   | qdrant_service.hybrid_search() |
| ChromaDB + BM25 pickle | Qdrant Cloud (dense + sparse)  |
| Manual RRF fusion      | Automatic RRF fusion           |
| Local storage (350MB)  | Cloud storage (0MB local)      |
| 3 separate services    | 1 unified service              |

📊 PERFORMANCE COMPARISON
Before (ChromaDB + BM25):

- Cold start: 10-15 seconds (load pickle)
- Search latency: ~300ms (local)
- Storage: 350MB RAM/disk
- Deployment: Requires persistent storage

After (Qdrant Cloud):

- Cold start: 1-2 seconds ✅
- Search latency: ~450ms (cloud) ⚠️ (acceptable)
- Storage: 0MB local ✅
- Deployment: Serverless-ready ✅


❌ app/services/ragservice.py           (replaced by qdrant_service)
❌ app/services/chromaservice.py         (replaced by qdrant_service)
❌ app/services/bm25service.py           (replaced by qdrant_service)
❌ app/utils/bm25_indexer.py            (no longer needed)
❌ .data/chromadb/                       (old local storage)
❌ .data/bm25_index.pkl                  (old BM25 pickle)




update requirements.txt pip install weasyprint==59.0 pydyf==0.6.0