#!/usr/bin/env python3
"""
End-to-End Exam Generation Pipeline Test
Tests the complete flow: API → JSON → Validation → PDF
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

def test_pipeline():
    """Test the complete exam generation pipeline"""
    
    print("\n" + "="*80)
    print("🧪 EXAM GENERATION PIPELINE TEST")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    results = {
        'api_health': False,
        'exam_generation': False,
        'json_validation': False,
        'student_pdf': False,
        'answer_key_pdf': False
    }
    
    base_url = "http://127.0.0.1:8001"
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Key": "dev_secret_key_12345"
    }
    
    # STEP 1: Health Check
    print("\n" + "-"*60)
    print("STEP 1: API Health Check")
    print("-"*60)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy and running")
            results['api_health'] = True
        else:
            print(f"❌ API returned status: {response.status_code}")
            return results
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the server is running on port 8001")
        return results
    
    # STEP 2: Generate Exam (Quick Test - 5 chapters)
    print("\n" + "-"*60)
    print("STEP 2: Exam Generation (Quick Test - 5 chapters)")
    print("-"*60)
    
    test_chapters = [
        "Real Numbers",
        "Polynomials",
        "Quadratic Equations",
        "Statistics",
        "Probability"
    ]
    
    payload = {
        "board": "CBSE",
        "class_num": 10,
        "subject": "Mathematics",
        "chapters": test_chapters
    }
    
    print(f"Generating exam with {len(test_chapters)} chapters...")
    print(f"Chapters: {', '.join(test_chapters)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/v1/exam/generate-board",
            json=payload,
            headers=headers,
            timeout=300
        )
        
        elapsed = time.time() - start_time
        print(f"Generation time: {elapsed:.1f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            exam = data.get('exam', {})
            
            # Save to file
            output_file = 'pipeline_test_exam.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(exam, f, indent=2, ensure_ascii=False)
            
            total_q = exam.get('metadata', {}).get('totalQuestions', 0)
            total_m = exam.get('metadata', {}).get('totalMarks', 0)
            
            print(f"✅ Exam generated successfully!")
            print(f"   Total Questions: {total_q}")
            print(f"   Total Marks: {total_m}")
            print(f"   Saved to: {output_file}")
            results['exam_generation'] = True
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return results
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (>5 minutes)")
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        return results
    
    # STEP 3: JSON Validation
    print("\n" + "-"*60)
    print("STEP 3: JSON Structure Validation")
    print("-"*60)
    
    try:
        with open('pipeline_test_exam.json', 'r', encoding='utf-8') as f:
            exam = json.load(f)
        
        # Check required fields
        checks = [
            ('metadata' in exam, 'metadata field exists'),
            ('sections' in exam, 'sections field exists'),
            (len(exam.get('sections', {})) > 0, 'has at least 1 section'),
        ]
        
        all_questions = []
        for section in exam.get('sections', {}).values():
            all_questions.extend(section.get('questions', []))
        
        checks.append((len(all_questions) > 0, 'has questions'))
        
        # Check question structure
        if all_questions:
            q = all_questions[0]
            checks.append(('text' in q, 'questions have text'))
            checks.append(('type' in q, 'questions have type'))
            checks.append(('correctAnswer' in q, 'questions have answer'))
        
        all_passed = True
        for passed, desc in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {desc}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ JSON validation passed!")
            results['json_validation'] = True
        else:
            print("❌ JSON validation failed")
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
    
    # STEP 4: Student PDF Generation
    print("\n" + "-"*60)
    print("STEP 4: Student PDF Generation")
    print("-"*60)
    
    try:
        from weasyprint import HTML
        from jinja2 import Environment, FileSystemLoader
        
        env = Environment(loader=FileSystemLoader('app/templates'))
        template = env.get_template('exam_pdf.html')
        html = template.render(exam=exam)
        
        pdf_path = 'pipeline_test_student.pdf'
        HTML(string=html).write_pdf(pdf_path)
        
        size = Path(pdf_path).stat().st_size
        print(f"✅ Student PDF generated: {pdf_path}")
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
        
        if size > 10000:
            results['student_pdf'] = True
        else:
            print("⚠️ PDF seems too small")
            
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
    
    # STEP 5: Answer Key PDF Generation
    print("\n" + "-"*60)
    print("STEP 5: Answer Key PDF Generation")
    print("-"*60)
    
    try:
        template = env.get_template('answer_key_pdf.html')
        html = template.render(exam=exam)
        
        pdf_path = 'pipeline_test_answer_key.pdf'
        HTML(string=html).write_pdf(pdf_path)
        
        size = Path(pdf_path).stat().st_size
        print(f"✅ Answer Key PDF generated: {pdf_path}")
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
        
        if size > 10000:
            results['answer_key_pdf'] = True
        else:
            print("⚠️ PDF seems too small")
            
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
    
    # SUMMARY
    print("\n" + "="*80)
    print("🎯 PIPELINE TEST RESULTS")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Pipeline is fully operational.")
    elif passed >= 3:
        print("\n⚠️ Most tests passed. Check failed items above.")
    else:
        print("\n❌ Pipeline has issues. Review errors above.")
    
    print("="*80 + "\n")
    
    return results

if __name__ == '__main__':
    test_pipeline()
