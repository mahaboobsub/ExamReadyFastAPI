# 🧹 Codebase Cleanup Guide

This document lists scripts that appear obsolete or redundant given the currently "Production Ready" pipeline.

## 🗑️ Safe to Delete (Redundant/Old)
These scripts have been superseded by newer, more robust versions.

1.  **`scripts/download_chemistry_units.py`**
    *   **Reason:** Project is currently Math-focused.

2.  **`scripts/process_maths_textbook.py`**
    *   **Reason:** Replaced by `reindex_all_textbooks_with_ocr.py` (which includes OCR/VLM).

3.  **`scripts/index_textbooks.py`** & **`scripts/index_all.py`**
    *   **Reason:** Replaced by `reindex_all_textbooks_with_ocr.py`.

4.  **`scripts/migrate_to_qdrant.py`**
    *   **Reason:** One-time migration script. Not needed for fresh setup.

5.  **`scripts/generate_test_exam.py`**
    *   **Reason:** Use `generate_exam_006.py` or `007` for testing now.

6.  **`scripts/apply_official_cbse_pattern.py`**
    *   **Reason:** Logic integrated into `BoardExamGenerator`.

## ⚠️ Check Before Deleting
1.  **`scripts/generate_full_14_chapter_exam.py`**
    *   Might be useful as a generic template, but `generate_exam_00X` scripts are more specific.

## ✅ KEEP (Critical Pipeline)
*   `download_ncert_maths.py`
*   `download_pyqs.py`
*   `download_sample_papers.py`
*   `reindex_all_textbooks_with_ocr.py` (The Master Ingestion Script)
*   `process_pyqs.py`
*   `process_sample_papers.py`
*   `generate_exam_006.py`, `007`, `008`
*   `validate_exam_quality.py`
*   `compare_exams.py`
*   `package_exams.py`
*   `repair_exam.py`
