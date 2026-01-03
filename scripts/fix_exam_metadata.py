#!/usr/bin/env python3
"""
Fix missing/invalid metadata in exam questions.
Applies intelligent defaults based on question type and context.
"""

import json
import sys
from pathlib import Path

def fix_question_metadata(question: dict, section_id: str) -> dict:
    """
    Fix missing or invalid metadata fields in a question.
    Returns: Fixed question dictionary
    """
    
    fixed = False
    
    # FIX 1: Chapter
    if not question.get('chapter') or question.get('chapter') in ['Unknown', None, '']:
        # Try to infer from context or use section default
        question['chapter'] = 'General Mathematics'
        fixed = True
        print(f"  ✓ Fixed chapter for Section {section_id}")
    
    # FIX 2: Bloom's Level
    if not question.get('bloomsLevel') or question.get('bloomsLevel') in ['Unknown', None, '']:
        # Infer from question type
        qtype = question.get('type', 'MCQ')
        blooms_map = {
            'MCQ': 'Remember',
            'AR': 'Understand',
            'VSA': 'Understand',
            'SA': 'Apply',
            'LA': 'Analyze',
            'CASE': 'Apply'
        }
        question['bloomsLevel'] = blooms_map.get(qtype, 'Apply')
        fixed = True
        print(f"  ✓ Fixed Bloom's level: {question['bloomsLevel']}")
    
    # FIX 3: Difficulty - Normalize invalid values
    difficulty = question.get('difficulty', '')
    
    if not difficulty or difficulty in ['Unknown', None, '']:
        # Map from Bloom's level
        blooms = question.get('bloomsLevel', 'Apply')
        diff_map = {
            'Remember': 'Easy',
            'Understand': 'Easy',
            'Apply': 'Medium',
            'Analyze': 'Hard',
            'Evaluate': 'Hard',
            'Create': 'Hard'
        }
        question['difficulty'] = diff_map.get(blooms, 'Medium')
        fixed = True
        print(f"  ✓ Fixed difficulty: {question['difficulty']}")
    
    elif difficulty not in ['Easy', 'Medium', 'Hard']:
        # Normalize variations like "Easy to Medium", "Medium to Hard"
        if 'easy' in difficulty.lower():
            question['difficulty'] = 'Easy'
        elif 'hard' in difficulty.lower():
            question['difficulty'] = 'Hard'
        else:
            question['difficulty'] = 'Medium'
        fixed = True
        print(f"  ✓ Normalized difficulty: '{difficulty}' → '{question['difficulty']}'")
    
    # FIX 4: Missing answer (critical issue)
    if not question.get('correctAnswer') or str(question.get('correctAnswer')).strip() == '':
        if question.get('type') in ['MCQ', 'AR'] and question.get('options'):
            # Default to first option with warning
            question['correctAnswer'] = question['options'][0]
            fixed = True
            print(f"  ⚠️ WARNING: Missing answer, defaulted to option A")
        else:
            question['correctAnswer'] = '[Answer to be filled]'
            fixed = True
            print(f"  ⚠️ WARNING: Missing answer, placeholder added")
    
    # FIX 5: Missing explanation
    if not question.get('explanation') or len(question.get('explanation', '')) < 10:
        question['explanation'] = f"The correct answer is {question.get('correctAnswer', 'as shown')}. This question tests understanding of {question.get('chapter', 'the topic')}."
        fixed = True
        print(f"  ✓ Added default explanation")
    
    # FIX 6: Ensure marks are set
    if not question.get('marks'):
        qtype = question.get('type', 'MCQ')
        marks_map = {
            'MCQ': 1, 'AR': 1, 'VSA': 2,
            'SA': 3, 'LA': 5, 'CASE': 4
        }
        question['marks'] = marks_map.get(qtype, 1)
        fixed = True
        print(f"  ✓ Fixed marks: {question['marks']}")
    
    return question, fixed

def fix_exam_metadata(exam_path: str, output_path: str = None):
    """
    Fix all metadata issues in exam JSON.
    """
    
    print("\n" + "="*80)
    print("🔧 FIXING EXAM METADATA")
    print("="*80)
    
    # Load exam
    with open(exam_path, 'r', encoding='utf-8') as f:
        exam = json.load(f)
    
    total_questions = 0
    fixed_questions = 0
    
    print(f"\nProcessing exam: {exam.get('metadata', {}).get('subject', 'Unknown')}")
    print(f"Sections: {len(exam.get('sections', {}))}")
    
    # Process each section
    for section_id, section in exam.get('sections', {}).items():
        print(f"\n📝 Section {section_id}: {section.get('name', '')}")
        
        questions = section.get('questions', [])
        total_questions += len(questions)
        
        for idx, question in enumerate(questions):
            question_num = idx + 1
            
            # Fix metadata
            fixed_q, was_fixed = fix_question_metadata(question, section_id)
            
            if was_fixed:
                fixed_questions += 1
                print(f"\n  Question {question_num}:")
                section['questions'][idx] = fixed_q
    
    # Summary
    print("\n" + "="*80)
    print("📊 FIX SUMMARY")
    print("="*80)
    print(f"Total Questions: {total_questions}")
    print(f"Questions Fixed: {fixed_questions}")
    print(f"Questions OK: {total_questions - fixed_questions}")
    
    # Save fixed exam
    if output_path is None:
        output_path = exam_path.replace('.json', '_fixed.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exam, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fixed exam saved to: {output_path}")
    print("="*80 + "\n")
    
    return output_path, fixed_questions

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_exam_metadata.py <exam.json> [output.json]")
        sys.exit(1)
    
    exam_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(exam_path).exists():
        print(f"❌ Error: File not found: {exam_path}")
        sys.exit(1)
    
    fix_exam_metadata(exam_path, output_path)
