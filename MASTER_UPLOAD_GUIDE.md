# 📚 Master Upload Pipeline - Quick Start Guide

## 🎯 Overview

This guide explains how to use the **Master Upload Pipeline** to process the 12 CBSE Class 10 Mathematics PDFs from `data/raw/cbse_class10_pdfs/maths/` and upload them to your Qdrant vector database.

---

## ✅ Pre-Flight Checklist

### 1. Verify PDFs are Present
```bash
python scripts/verify_pdf_inventory.py
```

**Expected Output:**
```
✅ All 12 expected PDFs present!
Total Size: 27.88 MB
```

### 2. Verify Environment Variables
Create/update `.env` file:
```env
# Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Qdrant
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=cbse_textbooks
```

### 3. Verify Qdrant Connection
```bash
python scripts/check_qdrant_coverage.py
```

---

## 🚀 Running the Master Upload

### Quick Start (Automated)
```bash
# From project root
python scripts/master_upload.py
```

### What It Does
1. **Scans** `data/raw/cbse_class10_pdfs/maths/` for PDFs
2. **Processes** each PDF using:
   - PyMuPDF for text extraction
   - Tesseract for OCR
   - Pix2Text for formula recognition
   - Gemini Vision for diagram analysis
3. **Chunks** content into semantic segments
4. **Embeds** chunks using Gemini text-embedding-004
5. **Uploads** to Qdrant collection

---

## 📊 Expected Processing Times

| PDF | Size | Estimated Time |
|-----|------|----------------|
| Real Numbers | 0.89 MB | ~2-3 min |
| Polynomials | 1.87 MB | ~3-4 min |
| Quadratic Equations | 1.17 MB | ~2-3 min |
| Triangles | 7.89 MB | ~8-10 min ⚠️ |
| Statistics | 3.12 MB | ~4-5 min |
| **TOTAL (12 PDFs)** | **27.88 MB** | **~45-60 min** |

⚠️ **Note:** Triangles PDF is the largest (7.89 MB) and may take longer.

---

## 📈 Sample Output

```
======================================================================
📚 MASTER PDF UPLOAD PIPELINE
======================================================================
Source Directory: data/raw/cbse_class10_pdfs/maths
Target Collection: cbse_textbooks
======================================================================

✅ Found 12 PDF files:
   • real_numbers.pdf                                  (  0.89 MB) → Real Numbers
   • polynomials.pdf                                   (  1.87 MB) → Polynomials
   ...

======================================================================
⚙️ INITIALIZING SERVICES
======================================================================
✅ Qdrant connection established
✅ Collection: cbse_textbooks

======================================================================
📄 PROCESSING PDFs
======================================================================

[1/12] real_numbers.pdf
Chapter: Real Numbers
----------------------------------------------------------------------
✅ Extracted 45 chunks

[2/12] polynomials.pdf
Chapter: Polynomials
----------------------------------------------------------------------
✅ Extracted 52 chunks

... (continues for all 12 PDFs)

======================================================================
📤 UPLOADING TO QDRANT
======================================================================
Total chunks to upload: 587

✅ UPLOAD COMPLETE!
   587 chunks uploaded to Qdrant

======================================================================
📊 UPLOAD SUMMARY REPORT
======================================================================

Processing Summary:
  Total PDFs:        12
  Successfully processed: 12
  Failed:            0
  Total Chunks:      587

📚 Chunks by Chapter:
----------------------------------------------------------------------
  Real Numbers                                        45 ( 7.7%)
  Polynomials                                         52 ( 8.9%)
  Pair of Linear Equations in Two Variables           48 ( 8.2%)
  Quadratic Equations                                 41 ( 7.0%)
  Some Applications of Trigonometry                   67 (11.4%)
  Triangles                                           72 (12.3%)
  Coordinate Geometry                                 34 ( 5.8%)
  Introduction to Trigonometry                        51 ( 8.7%)
  Surface Areas and Volumes                           38 ( 6.5%)
  Statistics                                          45 ( 7.7%)
  Probability                                         39 ( 6.6%)
  Mixed Content                                       55 ( 9.4%)

======================================================================
```

---

## 🔍 Verifying Upload Success

After the upload completes, verify the data:

```bash
# Check Qdrant status
python scripts/check_qdrant_coverage.py
```

**Expected Output:**
```
Collection: cbse_textbooks
Total Points: 587+
Chapters: 14 (11 from new PDFs + 3 from existing)
```

---

## 🛠️ Troubleshooting

### Issue: "Directory not found"
**Solution:**
```bash
# Verify path
ls -la data/raw/cbse_class10_pdfs/maths/
```

### Issue: "Qdrant connection failed"
**Solution:**
1. Check `.env` has correct `QDRANT_URL` and `QDRANT_API_KEY`
2. Verify Qdrant cluster is running
3. Test connection: `python scripts/check_qdrant_coverage.py`

### Issue: "OCR taking too long"
**Solution:**
- Ensure Tesseract is installed: `tesseract --version`
- For large PDFs (>5MB), expect 8-10 minutes
- Consider processing one PDF at a time for testing

### Issue: "Gemini API rate limit"
**Solution:**
- The script has built-in retry logic (5 attempts)
- If persistent, add delays between PDFs
- Check your Gemini API quota

---

## 📝 Next Steps After Upload

### 1. Test RAG Retrieval
```python
# scripts/test_qdrant_search.py
from app.services.qdrant_service import qdrant_service
import asyncio

async def test_search():
    await qdrant_service.initialize()
    
    results = await qdrant_service.search_textbooks(
        query="What is a quadratic equation?",
        limit=5,
        filters={"chapter": "Quadratic Equations"}
    )
    
    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. Score: {result.score:.4f}")
        print(f"   Text: {result.payload['text'][:100]}...")
    
    await qdrant_service.close()

asyncio.run(test_search())
```

### 2. Generate Test Exam
```bash
# Use the newly uploaded content
python scripts/generate_exam_007.py
```

### 3. Validate Quality
```bash
python scripts/validate_exam_quality.py test_output/exam_test_007.json
```

---

## 📚 Related Documentation

- **`TEAM_TESTING_GUIDE.md`** - Full data pipeline workflow
- **`CLEANUP_GUIDE.md`** - Scripts to keep/remove
- **`CODEBASE_SUMMARY.md`** - Complete project overview

---

## 🤝 Support

If you encounter issues:
1. Check logs in `board_gen_debug.log`
2. Verify environment variables in `.env`
3. Test individual PDFs first before batch processing

**Status:** Ready to run! 🚀
