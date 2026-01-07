# 🤖 AI Tutor Developer Guide (Onboarding)

Welcome to the **AI Tutor** feature! This guide details the architecture, data pipeline, and setup required to work on the RAG-based tutoring system.

---

## 🏗️ Architecture Overview

The AI Tutor uses a **Retrieval-Augmented Generation (RAG)** pipeline to answer student questions based on **NCERT Class 10 Mathematics textbooks**.

### Key Components
1.  **Source Data:** Official NCERT PDF Textbooks (stored in `data/textbooks/`).
2.  **Vector Database:** **Qdrant Cloud** (Collection: `cbse_textbooks`).
3.  **Hybrid Search:** Combines **Dense Vectors** (Semantic search) + **Sparse Vectors** (Keyword search).
4.  **OCR Stack:** PyMuPDF (Layout) + Tesseract (Text) + Pix2Text (Math Formulas) + Gemini Vision (Diagrams).
5.  **LLM:** Google Gemini 2.5 Flash used for both embedding generation and final answer synthesis.

---

## 🛠️ Step 1: Environment & Accounts

Before running any code, ensure you have the following accounts and config:

### 1. Qdrant Cloud Setup
1.  Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/).
2.  Create a **Free Tier Cluster**.
3.  Get your **Cluster URL** and **API Key**.

### 2. Google Gemini Setup
1.  Get an API Key from [Google AI Studio](https://aistudio.google.com/).

### 3. Local Configuration (`.env`)
Create a `.env` file in the project root:

```env
# Google Gemini
GOOGLE_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash

# Qdrant Vector DB
QDRANT_URL=https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=cbse_textbooks

# Timeout settings
QDRANT_TIMEOUT_SECONDS=60
```

---

## 📚 Step 2: Data Acquisition

We automate the downloading of official NCERT textbooks.

**Run Command:**
```bash
python scripts/download_ncert_maths.py
```

*   **Source:** `ncert.nic.in`
*   **Destination:** `data/textbooks/class_10/mathematics/`
*   **Files:** Downloads 14 PDF chapters (`jemh101.pdf` to `jemh114.pdf`).

---

## ⚙️ Step 3: Ingestion Pipeline (The "Heavy Lifting")

This is the most critical part for the AI Tutor. We convert raw PDFs into searchable vectors.

**Run Command:**
```bash
python scripts/master_upload.py
```

### What Happens Inside (`master_upload.py`):

1.  **OCR Extraction (`app/utils/pdfextractor.py`):**
    *   **Text:** Extracted via `PyMuPDF`.
    *   **Images/Diagrams:** Analyzed via `Gemini Vision` (if complex) or `Tesseract` (if simple text).
    *   **Math Formulas:** Processed via `Pix2Text` (latex conversion).

2.  **Chunking (`app/services/indexingservice.py`):**
    *   Text is split into semantic chunks.
    *   **Size:** 1000 characters.
    *   **Overlap:** 200 characters (preserves context).

3.  **Embedding (`app/services/geminiservice.py`):**
    *   Model: `models/text-embedding-004`.
    *   Dimension: **768**.

4.  **Qdrant Upload (`app/services/qdrant_service.py`):**
    *   **Collection:** `cbse_textbooks`
    *   **Vector Config:**
        *   **Dense:** 768 dimensions, `Cosine` distance.
        *   **Sparse:** `text-sparse` (BM25 based) for exact keyword matching.

---

## 🔍 Step 4: Retrieval Logic (How it works in App)

The AI Tutor endpoint resides in `app/routers/tutor.py`.

### How to Retrieve Chunks Code Snippet:
```python
from app.services.qdrant_service import qdrant_service

# 1. Initialize Service
await qdrant_service.initialize()

# 2. Perform Hybrid Search
results = await qdrant_service.hybrid_search(
    query="Explain Pythagoras theorem with formula",
    top_k=5,
    collection_name="cbse_textbooks"
)

# 3. Access Results
for chunk in results['chunks']:
    print(f"Confidence: {chunk['score']}")
    print(f"Text: {chunk['text']}")
    print(f"Source: {chunk['metadata']['source']}")
```

---

## ✅ Step 5: Verification

After setting up, verify that the AI Tutor has data to work with.

**Run Verification:**
```bash
python scripts/test_rag_accuracy.py
```

**Success Criteria:**
*   It should return specific text chunks relevant to the test query.
*   Qdrant Dashboard should show ~1500+ points in `cbse_textbooks`.

---

## 📜 Cheat Sheet: Essential Files

| File | Purpose |
|------|---------|
| `scripts/download_ncert_maths.py` | Download raw PDFs. |
| `scripts/master_upload.py` | **Main Pipeline:** Run this to populate DB. |
| `app/routers/tutor.py` | The API endpoint code you will work on. |
| `app/services/qdrant_service.py` | Handles Qdrant connection and search logic. |
| `tests/test_rag_accuracy.py` | Test script to check retrieval quality. |

---

**Happy Coding! 🚀**
