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

.\venv\Scripts\pip.exe list
Package                                  Version
---------------------------------------- ----------------
aiohappyeyeballs                         2.6.1
aiohttp                                  3.13.2
aiosignal                                1.4.0
albucore                                 0.0.24
albumentations                           2.0.8
annotated-types                          0.7.0
antlr4-python3-runtime                   4.9.3
anyio                                    4.12.0
asgiref                                  3.11.0
astroid                                  3.0.3
attrs                                    25.4.0
backoff                                  2.2.1
bcrypt                                   5.0.0
black                                    24.1.1
brotli                                   1.2.0
build                                    1.3.0
cachetools                               6.2.3
certifi                                  2025.11.12
cffi                                     2.0.0
charset-normalizer                       3.4.4
chroma-hnswlib                           0.7.3
chromadb                                 0.4.22
click                                    8.3.1
cnocr                                    2.3.2.2
cnstd                                    1.2.6.1
colorama                                 0.4.6
coloredlogs                              15.0.1
colorlog                                 6.10.1
contourpy                                1.3.3
cssselect2                               0.8.0
cycler                                   0.12.1
Deprecated                               1.3.1
dill                                     0.4.0
distro                                   1.9.0
doclayout_yolo                           0.0.4
durationpy                               0.10
fastapi                                  0.109.0
fastembed                                0.7.4
filelock                                 3.20.1
flatbuffers                              25.12.19
fonttools                                4.61.1
frozenlist                               1.8.0
fsspec                                   2025.12.0
gitdb                                    4.0.12
GitPython                                3.1.45
google-ai-generativelanguage             0.4.0
google-api-core                          2.28.1
google-auth                              2.43.0
google-generativeai                      0.3.2
googleapis-common-protos                 1.72.0
grpcio                                   1.76.0
grpcio-status                            1.62.3
grpcio-tools                             1.76.0
h11                                      0.16.0
h2                                       4.3.0
hf-xet                                   1.2.0
hpack                                    4.1.0
html5lib                                 1.1
httpcore                                 1.0.9
httptools                                0.7.1
httpx                                    0.28.1
huggingface-hub                          0.36.0
humanfriendly                            10.0
hyperframe                               6.1.0
idna                                     3.11
importlib_metadata                       8.4.0
importlib_resources                      6.5.2
iniconfig                                2.3.0
isort                                    5.13.2
Jinja2                                   3.1.6
joblib                                   1.5.2
json_repair                              0.54.3
kiwisolver                               1.4.9
kubernetes                               34.1.0
lightning-utilities                      0.15.2
loguru                                   0.7.3
markdown-it-py                           4.0.0
MarkupSafe                               2.1.5
matplotlib                               3.10.8
mccabe                                   0.7.0
mdurl                                    0.1.2
ml_dtypes                                0.5.4
mmh3                                     5.2.0
mpmath                                   1.3.0
multidict                                6.7.0
mypy_extensions                          1.1.0
networkx                                 3.6.1
nltk                                     3.9.2
numpy                                    1.26.4
oauthlib                                 3.3.1
omegaconf                                2.3.0
onnx                                     1.20.0
onnxruntime                              1.23.2
opencv-python                            4.11.0.86
opencv-python-headless                   4.11.0.86
opentelemetry-api                        1.27.0
opentelemetry-exporter-otlp-proto-common 1.27.0
opentelemetry-exporter-otlp-proto-grpc   1.27.0
opentelemetry-instrumentation            0.48b0
opentelemetry-instrumentation-asgi       0.48b0
opentelemetry-instrumentation-fastapi    0.48b0
opentelemetry-proto                      1.27.0
opentelemetry-sdk                        1.27.0
opentelemetry-semantic-conventions       0.48b0
opentelemetry-util-http                  0.48b0
optimum                                  2.0.0
optimum-onnx                             0.0.3
overrides                                7.7.0
packaging                                25.0
pandas                                   2.3.3
pathspec                                 0.12.1
pillow                                   11.3.0
pip                                      25.3
pix2text                                 1.1.4
platformdirs                             4.5.1
pluggy                                   1.6.0
polars                                   1.36.1
polars-runtime-32                        1.36.1
portalocker                              2.10.1
posthog                                  7.0.1
propcache                                0.4.1
proto-plus                               1.26.1
protobuf                                 6.33.2
psutil                                   7.1.3
pulsar-client                            3.8.0
py-cpuinfo                               9.0.0
py_rust_stemmers                         0.1.5
pyasn1                                   0.6.1
pyasn1_modules                           0.4.2
pyclipper                                1.4.0
pycparser                                2.23
pydantic                                 2.12.5
pydantic_core                            2.41.5
pydantic-settings                        2.1.0
pydyf                                    0.6.0
Pygments                                 2.19.2
pylint                                   3.0.3
PyMuPDF                                  1.23.8
PyMuPDFb                                 1.23.7
pyparsing                                3.2.5
pyphen                                   0.17.2
PyPika                                   0.48.9
pyproject_hooks                          1.2.0
pyreadline3                              3.5.4
pyspellchecker                           0.8.4
pytesseract                              0.3.13
pytest                                   7.4.3
pytest-asyncio                           0.21.1
python-dateutil                          2.9.0.post0
python-dotenv                            1.0.1
python-multipart                         0.0.6
pytorch-lightning                        2.6.0
pytz                                     2025.2
pywin32                                  311
PyYAML                                   6.0.3
qdrant-client                            1.12.1
rank-bm25                                0.2.2
rapidocr                                 3.4.3
redis                                    5.0.1
regex                                    2025.11.3
requests                                 2.32.5
requests-oauthlib                        2.0.0
rich                                     14.2.0
rsa                                      4.9.1
safetensors                              0.7.0
scikit-learn                             1.8.0
scipy                                    1.16.3
seaborn                                  0.13.2
sentence-transformers                    2.3.1
sentencepiece                            0.2.1
sentry-sdk                               2.47.0
setuptools                               80.9.0
shapely                                  2.1.2
shellingham                              1.5.4
simsimd                                  6.5.3
six                                      1.17.0
smmap                                    5.0.2
starlette                                0.35.1
stringzilla                              4.5.1
sympy                                    1.14.0
tenacity                                 9.1.2
thop                                     0.1.1-2209072238
threadpoolctl                            3.6.0
tinycss2                                 1.5.1
tokenizers                               0.22.1
tomlkit                                  0.13.3
torch                                    2.9.1
torchmetrics                             1.8.2
torchvision                              0.24.1
tqdm                                     4.67.1
transformers                             4.57.3
typer                                    0.20.0
typer-slim                               0.21.0
typing_extensions                        4.15.0
typing-inspection                        0.4.2
tzdata                                   2025.3
ultralytics                              8.3.239
ultralytics-thop                         2.0.18
Unidecode                                1.4.0
urllib3                                  2.6.2
uvicorn                                  0.27.0
wandb                                    0.23.1
watchfiles                               1.1.1
weasyprint                               59.0
webencodings                             0.5.1
websocket-client                         1.9.0
websockets                               15.0.1
win32_setctime                           1.2.0
wrapt                                    1.17.3
yarl                                     1.22.0
zipp                                     3.23.0
zopfli                                   0.4.0
PS C:\Users\Lenovo\Desktop\examready-fastapi> 



# Step 1: Test single exam generation (NO storage yet)
python scripts/generate_single_test_exam.py

# This will:
# ├─ Generate 1 exam using LLM
# ├─ Run validation (all 10 checks)
# ├─ Output detailed report
# └─ Save to: test_output/exam_validation_report.json

# Step 2: Review validation report together
# You share the JSON, I analyze:
# - Chapter coverage (14/14?)
# - Bloom's distribution (within ±3%?)
# - Quality score (≥0.85?)
# - CBSE pattern match (38Q, 80M, 5 sections?)

# Step 3: IF PASS → Store in Qdrant
# python scripts/store_validated_exam.py test_output/exam_xyz.json
