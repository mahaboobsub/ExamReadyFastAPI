# 🎯 Dual-Collection Strategy - Complete Execution Plan

## 📊 Architecture Overview

You will have **TWO Qdrant collections** serving different purposes:

| Collection | Purpose | Content Type | Use Case |
|------------|---------|--------------|----------|
| **`cbse_textbooks`** | AI Tutor / RAG | Text chunks (paragraphs) | Answer student questions with context |
| **`cbse_questions_v2`** | Exam Generation | Individual questions + metadata | Generate CBSE-compliant exams with rules |

---

## 🚀 PHASE A: Textbook Chunks (For AI Tutor) - DO THIS FIRST

### Purpose
Build general knowledge base for the AI Tutor feature using existing OCR pipeline.

### ✅ Execution Steps

```bash
# 1. Verify PDFs are present
python scripts/verify_pdf_inventory.py

# 2. Run textbook chunk upload (45-60 minutes)
python scripts/master_upload.py

# 3. Verify upload success
python scripts/check_qdrant_coverage.py
```

### 📊 Expected Results
- **~500-700 text chunks** uploaded to `cbse_textbooks`
- **AI Tutor** can now answer questions using textbook context
- **Exam generation** continues to work with existing logic

### ⏱️ Time Required
- **45-60 minutes** (OCR processing time)

---

## 🚀 PHASE B: Question-Level Index (For Exam Rules) - DO THIS AFTER PHASE A

### Purpose
Build CBSE-specific question bank with metadata to enforce exam generation rules (Q19-Q20 AR, Section D distribution, etc.)

### ✅ Execution Steps

#### **Step 1: Setup Question Collection** (2 minutes)
```bash
python scripts/setup_question_collection.py
```

**What it does:**
- Creates new Qdrant collection: `cbse_questions_v2`
- Sets up payload indexes for filtering (chapter, type, difficulty, section, blooms)
- Configures for Gemini embeddings (768 dimensions)

---

#### **Step 2: Extract Questions** (60-90 minutes)
```bash
python scripts/extract_questions_from_pdfs.py
```

**What it does:**
- Processes all 12 PDFs page-by-page
- Uses Gemini to identify individual questions
- Extracts solutions marked as `[Sol: ...]`
- Saves to `data/processed/questions/all_questions_raw.json`

**Expected Output:**
```
📊 EXTRACTION SUMMARY
Total PDFs:        12
Processed:         12
Failed:            0
Total Questions:   ~500-700
```

**⚠️ Note:** This is the longest step due to Gemini API calls per page.

---

#### **Step 3: Classify Questions** (30-45 minutes)
```bash
python scripts/classify_questions.py
```

**What it does:**
- Reads raw questions from Step 2
- Uses Gemini to classify each question:
  - `question_type`: MCQ, VSA, SA, LA, Assertion-Reason, Proof, Case Study
  - `difficulty`: Easy, Medium, Hard
  - `blooms_level`: Remember, Understand, Apply, Analyze, Evaluate
  - `section`: A, B, C, D, E
  - `keywords`: List of key concepts
- Saves to `data/processed/questions/all_questions_classified.json`

**Expected Output:**
```
By Question Type:
  MCQ                   89 (15.2%)
  VSA                  121 (20.6%)
  SA                   185 (31.5%)
  LA                   125 (21.3%)
  Assertion-Reason      45 ( 7.7%)
  Proof                 67 (11.4%)
```

---

#### **Step 4: Upload to Qdrant** (15-20 minutes)
```bash
python scripts/upload_questions_to_qdrant.py
```

**What it does:**
- Reads classified questions from Step 3
- Generates embeddings using Gemini text-embedding-004
- Uploads to `cbse_questions_v2` collection
- Includes full metadata for filtering

**Expected Output:**
```
📊 UPLOAD SUMMARY
Total Questions:   587
Uploaded:          587
Failed:            0

Qdrant Collection: cbse_questions_v2
Points Count:      587
```

---

### ⏱️ Total Time for Phase B
- **Setup:** 2 min
- **Extract:** 60-90 min
- **Classify:** 30-45 min
- **Upload:** 15-20 min
- **TOTAL:** ~2-3 hours

---

## 📋 Verification Checklist

After completing both phases, verify:

### ✅ Phase A (Textbook Chunks)
```bash
python scripts/check_qdrant_coverage.py
```

Expected:
```
Collection: cbse_textbooks
Points Count: 500-700 (chunks)
```

### ✅ Phase B (Questions)
```python
# Quick test script
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

info = client.get_collection("cbse_questions_v2")
print(f"Questions Collection: {info.points_count} questions")

# Test query with filters
results = client.scroll(
    collection_name="cbse_questions_v2",
    scroll_filter={
        "must": [
            {"key": "question_type", "match": {"value": "Assertion-Reason"}},
            {"key": "section", "match": {"value": "A"}}
        ]
    },
    limit=5
)

print(f"\nAssertion-Reason questions in Section A: {len(results[0])}")
for idx, point in enumerate(results[0], 1):
    print(f"{idx}. {point.payload['question_text'][:80]}...")
```

---

## 🎯 Next Steps: Use the Question Collection

### Update Exam Generator to Use Questions

Modify `app/services/board_exam_generator.py` to query `cbse_questions_v2`:

```python
# OLD: Query textbook chunks
results = await self.qdrant.search_textbooks(
    query="quadratic equations",
    limit=10
)

# NEW: Query classified questions
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = self.qdrant.client.scroll(
    collection_name="cbse_questions_v2",
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="chapter",
                match=MatchValue(value="Quadratic Equations")
            ),
            FieldCondition(
                key="question_type",
                match=MatchValue(value="Assertion-Reason")
            ),
            FieldCondition(
                key="section",
                match=MatchValue(value="A")
            )
        ]
    ),
    limit=2  # For Q19-Q20
)
```

### Fix Q19-Q20 Assertion-Reason Rule
```python
# In board_exam_generator.py, Section A logic:

# For Q19-Q20, explicitly require Assertion-Reason
if question_number in [19, 20]:
    ar_questions = self.qdrant.client.scroll(
        collection_name="cbse_questions_v2",
        scroll_filter=Filter(
            must=[
                FieldCondition(key="question_type", match=MatchValue(value="Assertion-Reason")),
                FieldCondition(key="section", match=MatchValue(value="A"))
            ]
        ),
        limit=2
    )
    
    # Use AR questions
    questions.extend([q.payload for q in ar_questions[0]])
```

### Fix Section D Chapter Distribution
```python
# Track chapter usage in Section D
section_d_chapters = Counter()

for la_question in section_d_questions:
    chapter = la_question.payload['chapter']
    
    # Rule: Max 2 questions per chapter in Section D
    if section_d_chapters[chapter] >= 2:
        continue  # Skip this question
    
    section_d_chapters[chapter] += 1
    selected_questions.append(la_question)
```

---

## 🔄 Summary

| Phase | Purpose | Time | Output | Next Use |
|-------|---------|------|--------|----------|
| **A** | AI Tutor | 45-60 min | 500-700 chunks in `cbse_textbooks` | AI Tutor answers questions |
| **B** | Exam Rules | 2-3 hours | 500-700 questions in `cbse_questions_v2` | Fix Q19-Q20, Section D rules |

**Total Setup Time:** ~3-4 hours
**Long-term Value:** Complete infrastructure for both tutoring AND rule-based exam generation

---

## 📞 Troubleshooting

### "Collection already exists"
**Solution:** Delete old collection first:
```python
from qdrant_client import QdrantClient
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
client.delete_collection("cbse_questions_v2")
```

### "Gemini API rate limit"
**Solution:** Scripts have built-in 0.2-0.5s delays. Wait and retry.

### "No questions extracted"
**Solution:** Check PDF quality. Some pages may be images - OCR will handle them.

---

**Status:** Ready to execute Phase A immediately! 🚀
