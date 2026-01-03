# 🧹 Codebase Cleanup Guide

## Overview
This guide categorizes all files into: **KEEP** vs **DELETE**

---

## 📁 ROOT DIRECTORY FILES

### ✅ KEEP (Essential)
| File | Reason |
|------|--------|
| `.env` | Environment configuration |
| `.gitignore` | Git ignore rules |
| `Dockerfile` | Docker deployment |
| `README.md` | Project documentation |
| `TESTING_GUIDE.md` | Team testing guide |
| `requirements.txt` | Python dependencies |
| `files_md.sh` | Code extraction utility |

### ❌ DELETE (Generated/Debug/Temp)
| File | Size | Reason |
|------|------|--------|
| `backup_textbooks_20260103_110043.json` | 2.1 MB | One-time backup |
| `board_gen_debug.log` | 2 KB | Debug log |
| `code3.txt` | 5.4 MB | Generated code dump |
| `debug_vision_test.png` | 305 KB | Debug image |
| `exam_analysis.txt` | 2 KB | Temp analysis output |
| `exam_quality_report.json` | 0.4 KB | Temp report |
| `full_14_chapter_exam.json` | 66 KB | Generated exam (raw) |
| `full_14_chapter_exam_CLEANED.json` | 65 KB | Intermediate version |
| `full_14_chapter_exam_FINAL.json` | 64 KB | Can regenerate |
| `full_14_chapter_exam_fixed.json` | 67 KB | Intermediate version |
| `latest_generated_board_exam.json` | 63 KB | Old generated exam |
| `latest_generated_board_exam_fixed.json` | 59 KB | Old fixed version |
| `pipeline_test_exam.json` | 63 KB | Test output |
| `pipeline_test_exam_FIXED.json` | 56 KB | Test output |
| `pipeline_test_exam_OFFICIAL.json` | 63 KB | Test output |
| `pipeline_test_answer_key.pdf` | 123 KB | Test output |
| `pipeline_test_student.pdf` | 66 KB | Test output |
| `qdrant_coverage_report.json` | 2 KB | Temp report |
| `CBSE_Class10_Maths_BoardExam_*.pdf` | 28 KB | Old generated PDFs |

**Space saved: ~8.5 MB**

---

## 📁 /scripts DIRECTORY (62 files)

### ✅ KEEP - Core Pipeline (12 files)
| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `download_ncert_maths.py` | Download textbooks |
| `download_pyqs.py` | Download PYQs |
| `download_sample_papers.py` | Download sample papers |
| `process_maths_textbook.py` | Index textbooks |
| `process_pyqs.py` | Index PYQs |
| `process_sample_papers.py` | Index sample papers |
| `index_textbooks.py` | Create Qdrant indexes |
| `check_qdrant_coverage.py` | Verify data coverage |
| `test_pipeline.py` | End-to-end test |
| `validate_exam_quality.py` | Quality validation |
| `generate_full_14_chapter_exam.py` | Full exam generation |

### ⚠️ OPTIONAL - Useful Utilities (10 files)
| File | Purpose | Keep? |
|------|---------|-------|
| `analyze_exam.py` | Exam structure analysis | ✅ Useful |
| `backup_qdrant_collection.py` | Backup Qdrant data | ✅ Useful |
| `clear_textbook_collection.py` | Clear Qdrant collection | ✅ Useful |
| `fix_exam_metadata.py` | Fix missing metadata | ✅ Useful |
| `apply_official_cbse_pattern.py` | Apply CBSE pattern | ✅ Useful |
| `download_chemistry_units.py` | For future science | ✅ Keep |
| `seed_question_bank.py` | Seed questions | ⚠️ Maybe |
| `reindex_all_textbooks_with_ocr.py` | OCR indexing | ⚠️ Maybe |
| `migrate_to_qdrant.py` | Migration script | ⚠️ Maybe |
| `index_all.py` | Batch indexing | ⚠️ Maybe |

### ❌ DELETE - Debug/Duplicate/Unused (40 files)
| File | Reason |
|------|--------|
| `check_chapter_names.py` | Debug script |
| `check_chapters.py` | Debug script |
| `check_pdf_images.py` | Debug script |
| `check_qdrant_data.py` | Duplicate of check_qdrant_coverage |
| `create_qdrant_indexes.py` | Duplicate of index_textbooks |
| `debug_exam.py` | Debug script |
| `debug_exam_queries.py` | Debug script |
| `debug_qdrant_filters.py` | Debug script |
| `diagnose_pdf_template.py` | Debug script |
| `download_maths_units.py` | Duplicate of download_ncert_maths |
| `download_pdfs.py` | Generic/unused |
| `download_pyqs_backup.py` | Backup/duplicate |
| `final_audit.py` | One-time audit |
| `final_cleanup.py` | One-time cleanup |
| `fix_board_indexes.py` | One-time fix |
| `fix_cbse_pattern.py` | Superseded by apply_official |
| `fix_section_e.py` | One-time fix |
| `list_models.py` | Debug script |
| `process_maths_textbook_v2.py` | Old version |
| `quick_summary.py` | Debug script |
| `quick_verify.py` | Debug script |
| `seed_math_quick.py` | Old seeding script |
| `test_chem_rag.py` | Debug test |
| `test_extraction.py` | Debug test |
| `test_formula_extraction.py` | Debug test |
| `test_maths_rag.py` | Debug test |
| `test_ocr.py` | Debug test |
| `test_rag.py` | Debug test |
| `test_rag_retrieval.py` | Debug test |
| `test_services.py` | Debug test |
| `test_vision.py` | Debug test |
| `validate_system.py` | Debug validation |
| `validate_v1_advanced_metrics.py` | Old validation |
| `validate_v1_board.py` | Old validation |
| `validate_v1_metrics.py` | Old validation |
| `validate_v2_metrics.py` | Old validation |
| `verify_clean_collection.py` | Debug script |
| `verify_downloads.py` | Debug script |
| `verify_qdrant_status.py` | Debug script |
| `visual_verification.py` | Debug script |

---

## 📁 /app DIRECTORY (All Essential)

### ✅ KEEP ALL - Core Application
| Directory | Files | Purpose |
|-----------|-------|---------|
| `app/config/` | 4 files | Settings, prompts, templates |
| `app/middleware/` | 2 files | Logging middleware |
| `app/models/` | 6 files | Pydantic models |
| `app/routers/` | 6 files | API endpoints |
| `app/services/` | 18 files | Business logic |
| `app/templates/` | 2 files | PDF templates |
| `app/utils/` | 3 files | Utilities |
| `app/main.py` | 1 file | FastAPI entry |

**DO NOT DELETE ANYTHING FROM /app**

---

## 📁 /tests DIRECTORY

### ✅ KEEP (For Testing)
| File | Purpose |
|------|---------|
| `test_integration.py` | Integration tests |
| `test_exam_logic.py` | Exam logic tests |
| `test_blooms_distribution.py` | Bloom's tests |
| `run_all.py` | Test runner |

### ❌ DELETE (Debug/Unused)
| File | Reason |
|------|--------|
| `test_flashcards_api.py` | Feature not used |
| `test_quiz_api.py` | Feature not used |
| `test_tutor_api.py` | Feature not used |
| `test_error_handling.py` | Debug tests |

---

## 📁 /validation_results DIRECTORY

### ❌ DELETE ENTIRE FOLDER
All 5 JSON files are old validation outputs - can regenerate.

---

## 📁 /data DIRECTORY

### ✅ KEEP Structure (Empty for teammate)
```
data/
  textbooks/class_10/mathematics/  # PDFs go here
  pyq/class_10/mathematics/        # PYQs go here
  sample_papers/class_10/mathematics/  # Sample papers go here
```

### ❌ DELETE
Any existing PDFs (teammate will download fresh)

---

## 📁 OTHER DIRECTORIES

### ❌ DELETE
| Directory | Reason |
|-----------|--------|
| `.pytest_cache/` | Cache - regenerates |
| `__pycache__/` | Cache - regenerates |
| `.data/` | Unknown/unused |
| `venv/` | Teammate creates own |

---

## 🚀 CLEANUP COMMANDS

### Quick Cleanup Script
```powershell
# Run from project root

# 1. Delete root temp files
Remove-Item -Force backup_textbooks_*.json
Remove-Item -Force board_gen_debug.log
Remove-Item -Force code*.txt
Remove-Item -Force debug_*.png
Remove-Item -Force exam_*.txt
Remove-Item -Force exam_*.json
Remove-Item -Force full_*.json
Remove-Item -Force latest_*.json
Remove-Item -Force pipeline_*.json
Remove-Item -Force pipeline_*.pdf
Remove-Item -Force qdrant_*.json
Remove-Item -Force CBSE_*.pdf

# 2. Delete validation_results folder
Remove-Item -Recurse -Force validation_results/

# 3. Delete cache folders
Remove-Item -Recurse -Force .pytest_cache/
Remove-Item -Recurse -Force .data/

# 4. Clean __pycache__ folders
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 5. Don't delete venv - leave for teammate to create
```

---

## 📊 SUMMARY

| Category | Count | Size | Action |
|----------|-------|------|--------|
| Root temp files | 19 | ~8.5 MB | DELETE |
| Debug scripts | 40 | ~100 KB | DELETE |
| Core scripts | 22 | ~80 KB | KEEP |
| App files | 43 | ~150 KB | KEEP |
| Tests (useful) | 4 | ~20 KB | KEEP |
| Tests (unused) | 4 | ~15 KB | DELETE |
| Validation results | 5 | ~10 KB | DELETE |

**Before cleanup:** ~15 MB of files
**After cleanup:** ~300 KB of essential code

---

## ✅ FINAL KEEP LIST

### Essential Files (Share with teammate)
```
examready-fastapi/
├── .env.example          # Template (create from .env)
├── .gitignore
├── Dockerfile
├── README.md
├── TESTING_GUIDE.md
├── requirements.txt
├── app/                  # ALL files
├── scripts/
│   ├── download_ncert_maths.py
│   ├── download_pyqs.py
│   ├── download_sample_papers.py
│   ├── download_chemistry_units.py
│   ├── process_maths_textbook.py
│   ├── process_pyqs.py
│   ├── process_sample_papers.py
│   ├── index_textbooks.py
│   ├── check_qdrant_coverage.py
│   ├── test_pipeline.py
│   ├── validate_exam_quality.py
│   ├── analyze_exam.py
│   ├── generate_full_14_chapter_exam.py
│   ├── apply_official_cbse_pattern.py
│   ├── fix_exam_metadata.py
│   ├── backup_qdrant_collection.py
│   └── clear_textbook_collection.py
├── tests/
│   ├── test_integration.py
│   ├── test_exam_logic.py
│   └── run_all.py
└── data/                 # Empty folder structure
    └── textbooks/class_10/mathematics/
```
