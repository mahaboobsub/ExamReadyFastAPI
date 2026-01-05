# 🧪 End-to-End Pipeline Testing Guide

This guide is for teammates to validate the complete ExamReady pipeline, from Data Ingestion to Exam Generation.

## 🛑 Prerequisite (Setup Environment)
1. **Python Setup:**
   ```bash
   pip install -r requirements.txt
   # Ensure Tesseract OCR is installed on system and in PATH
   ```

2. **Qdrant Cloud Setup (CRITICAL):**
   *   Create a FREE account at [cloud.qdrant.io](https://cloud.qdrant.io).
   *   Create a Cluster (Free Tier).
   *   Get the **API Key** and **Cluster URL**.
   *   Create a `.env` file in the project root:
     ```env
     QDRANT_URL=https://your-cluster-url.qdrant.tech
     QDRANT_API_KEY=your-api-key-here
     GOOGLE_API_KEY=your-gemini-key
     ```

3. **Verify Connection:**
   Run `scripts/check_qdrant_coverage.py` to see if connection works (it will show 0 points initially).

---

## 📂 Phase 1: Data Acquisition (Download)
Run these scripts to fetch the raw PDF data.

1. **NCERT Textbooks:**
   ```bash
   python scripts/download_ncert_maths.py
   # Downloads to data/textbooks/class_10/mathematics
   ```

2. **Previous Year Questions (PYQs):**
   ```bash
   python scripts/download_pyqs.py
   # Downloads to data/pyqs/class_10/mathematics
   ```

3. **Sample Papers:**
   ```bash
   python scripts/download_sample_papers.py
   # Downloads to data/sample_papers/class_10/mathematics
   ```

---

## 🧠 Phase 2: Ingestion & Extraction (OCR/VLM Processing)
This phase extracts text, formulas, and images using the full stack (Tesseract, Pix2Text, Gemini Vision). It chunks and embeds data into Qdrant.

**⚠️ Warning:** This is compute-intensive and may take time.

1. **Process Textbooks (Full OCR):**
   ```bash
   python scripts/reindex_all_textbooks_with_ocr.py
   ```
   *   Uses `pix2text` for mixed formula/text.
   *   Uses `Gemini Vision` for complex diagrams.
   *   Stores in Qdrant collection `cbse_textbooks`.

2. **Process PYQs:**
   ```bash
   python scripts/process_pyqs.py
   ```

3. **Process Sample Papers:**
   ```bash
   python scripts/process_sample_papers.py
   ```

---

## 📝 Phase 3: Exam Generation (Testing 005-008)
Test the generation logic using the stored RAG context.
**Do NOT** run Board or Custom mode endpoints manually; use these scripts to simulate the specific exam definitions.

### 1. Exam 005 (Production Ready)
   ```bash
   python scripts/finalize_exam_005.py
   # OR python scripts/generate_full_14_chapter_exam.py
   ```

### 2. Exam 006 (Confidence Builder - Easy)
   ```bash
   python scripts/generate_exam_006.py
   ```

### 3. Exam 007 (Challenger - Hard)
   ```bash
   python scripts/generate_exam_007.py
   ```
   *   **Note:** This script uses an `avoid_list` to exclude topics from 005/006.

### 4. Exam 008 (Board Simulator - Standard)
   ```bash
   python scripts/generate_exam_008.py
   ```
   *   **Note:** This script uses an `avoid_list` to exclude topics from 005/006/007.

---

## ✅ Phase 4: Validation & Packing
After generating exams, validate them.

1. **Check Quality Scores:**
   ```bash
   python scripts/validate_exam_quality.py test_output/exam_test_007.json
   ```

2. **Check Uniqueness (Cross-Exam):**
   ```bash
   python scripts/compare_exams.py
   ```

3. **Package for Delivery:**
   ```bash
   python scripts/package_exams.py
   ```
   *   Creates `exam_papers_for_review_v1/`.

---

## 🛠️ Troubleshooting
- **RAG Connection Error?** Ensure Qdrant is running. The scripts use Lazy Initialization.
- **Missing Answers in JSON?** Run `python scripts/repair_exam.py <json_file>` to patch metadata using LLM.
