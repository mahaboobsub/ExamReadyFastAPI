"""
Extract individual questions from CBSE PDFs using Gemini
IMPROVED VERSION with robust JSON parsing
"""
import asyncio
import json
import os
import sys
from pathlib import Path
import fitz  # PyMuPDF
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.geminiservice import GeminiService


PDF_DIR = Path("data/raw/cbse_class10_pdfs/maths")
OUTPUT_DIR = Path("data/processed/questions")


# Chapter mapping
CHAPTER_MAP = {
    "real_numbers.pdf": "Real Numbers",
    "polynomials.pdf": "Polynomials",
    "PAIR OF LINEAR EQUATIONS IN TWO VARIABLES.pdf": "Pair of Linear Equations in Two Variables",
    "quadratic_equations.pdf": "Quadratic Equations",
    "SOME APPLICATIONS OF TRIGONOMETRY.pdf": "Some Applications of Trigonometry",
    "triangles.pdf": "Triangles",
    "CO-ORDINATE GEOMETRY.pdf": "Coordinate Geometry",
    "INTRODUCTION TO TRIGONOMETRY.pdf": "Introduction to Trigonometry",
    "SURFACE_AREAS_AND_VOLUMES.pdf": "Surface Areas and Volumes",
    "statistics.pdf": "Statistics",
    "probability.pdf": "Probability",
    "Full Text Book Markings and Synopsis-Class X.pdf": "Mixed Content"
}


def extract_json_from_response(text: str):
    """
    Robustly extract JSON from Gemini response
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Find JSON array
    start = text.find('[')
    end = text.rfind(']')
    
    if start == -1 or end == -1:
        return None
    
    json_str = text[start:end+1]
    
    # Try to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try to fix common issues
        # Replace smart quotes
        json_str = json_str.replace('"', '"').replace('"', '"')
        json_str = json_str.replace(''', "'").replace(''', "'")
        
        try:
            return json.loads(json_str)
        except:
            return None


async def extract_questions_from_pdf(pdf_path: Path, chapter_name: str, gemini: GeminiService):
    """
    Extract questions from a single PDF
    """
    print(f"\n📄 Processing: {pdf_path.name}")
    print(f"   Chapter: {chapter_name}")
    print("-"*70)
    
    doc = fitz.open(pdf_path)
    all_questions = []
    successful_pages = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        # Skip if page has no content
        if len(text.strip()) < 50:
            continue
        
        # Simpler, more direct prompt
        prompt = f"""Extract CBSE Class 10 Math questions from this page. Return ONLY a JSON array.

Format: [{{"q": "question text", "sol": "solution if present or null", "marks": number or null}}]

Page text:
{text[:3500]}

Return JSON array only, no other text."""
        
        try:
            response = await gemini.generate(prompt, temperature=0.0, max_tokens=2000)
            
            questions = extract_json_from_response(response)
            
            if questions and len(questions) > 0:
                # Convert to full format
                for q in questions:
                    full_q = {
                        'question_text': q.get('q', ''),
                        'solution': q.get('sol'),
                        'marks': q.get('marks'),
                        'question_number': str(len(all_questions) + 1),
                        'has_sub_parts': False,
                        'source_file': pdf_path.name,
                        'chapter': chapter_name,
                        'page_number': page_num + 1
                    }
                    all_questions.append(full_q)
                
                successful_pages += 1
                print(f"   Page {page_num + 1}: {len(questions)} questions ✅")
            
        except Exception as e:
            # Silent fail - don't spam errors
            pass
        
        # Rate limiting
        await asyncio.sleep(0.3)
    
    success_rate = (successful_pages / len(doc) * 100) if len(doc) > 0 else 0
    print(f"   ✅ Total: {len(all_questions)} questions from {successful_pages}/{len(doc)} pages ({success_rate:.1f}% success)")
    return all_questions


async def main():
    """
    Main extraction pipeline
    """
    print("="*70)
    print("📚 QUESTION EXTRACTION PIPELINE v2 (IMPROVED)")
    print("="*70)
    print(f"Source: {PDF_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize Gemini
    gemini = GeminiService()
    
    # Get PDFs
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    
    if len(pdf_files) == 0:
        print("❌ No PDFs found!")
        return
    
    print(f"\n✅ Found {len(pdf_files)} PDFs\n")
    
    all_questions = []
    stats = {
        'total_pdfs': len(pdf_files),
        'processed': 0,
        'failed': 0,
        'total_questions': 0,
        'total_pages': 0,
        'successful_pages': 0
    }
    
    # Process each PDF
    for idx, pdf_path in enumerate(pdf_files, 1):
        chapter_name = CHAPTER_MAP.get(pdf_path.name, "Unknown")
        
        print(f"\n[{idx}/{len(pdf_files)}]")
        
        try:
            questions = await extract_questions_from_pdf(pdf_path, chapter_name, gemini)
            
            all_questions.extend(questions)
            stats['processed'] += 1
            stats['total_questions'] += len(questions)
            
            # Save per-PDF results
            pdf_output = OUTPUT_DIR / f"{pdf_path.stem}_questions.json"
            with open(pdf_output, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            stats['failed'] += 1
            continue
    
    # Save all questions
    all_output = OUTPUT_DIR / "all_questions_raw.json"
    with open(all_output, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 EXTRACTION SUMMARY")
    print("="*70)
    print(f"Total PDFs:        {stats['total_pdfs']}")
    print(f"Processed:         {stats['processed']}")
    print(f"Failed:            {stats['failed']}")
    print(f"Total Questions:   {stats['total_questions']}")
    print(f"\n✅ Saved to: {all_output}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
