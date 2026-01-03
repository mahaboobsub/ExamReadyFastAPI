#!/usr/bin/env python3
"""
Quality inspection script for generated exam papers.
Checks if exam is good enough before storing in Qdrant.
"""

import json
import sys
from pathlib import Path

def inspect_exam_quality(exam_path: str):
    """
    Analyze exam quality across multiple dimensions.
    Returns: Pass/Fail decision + detailed metrics
    """
    
    print("\n" + "="*80)
    print("🔍 EXAM QUALITY INSPECTION REPORT")
    print("="*80)
    
    # Load exam
    with open(exam_path, 'r', encoding='utf-8') as f:
        exam = json.load(f)
    
    metadata = exam.get('metadata', {})
    sections = exam.get('sections', {})
    
    # Collect all questions
    all_questions = []
    for section_id, section in sections.items():
        for q in section.get('questions', []):
            q['section'] = section_id
            all_questions.append(q)
    
    print(f"\n📊 BASIC STATS")
    print("-"*80)
    print(f"Total Questions: {len(all_questions)}")
    print(f"Total Marks: {metadata.get('totalMarks', 0)}")
    print(f"Sections: {len(sections)}")
    print(f"Generation Time: {metadata.get('generationTimeMs', 0)/1000:.1f} seconds")
    
    # Quality metrics
    issues = {
        'mock_questions': [],
        'missing_chapter': [],
        'missing_blooms': [],
        'missing_difficulty': [],
        'missing_answer': [],
        'missing_explanation': [],
        'short_text': [],
        'wrong_options': []
    }
    
    print(f"\n🔍 DETAILED QUALITY CHECK")
    print("-"*80)
    
    for idx, q in enumerate(all_questions, 1):
        q_id = f"Q{idx} (Section {q['section']})"
        
        # Check 1: Mock questions
        if 'MOCK' in q.get('text', '').upper():
            issues['mock_questions'].append(q_id)
        
        # Check 2: Chapter metadata
        if not q.get('chapter') or q.get('chapter') == 'Unknown':
            issues['missing_chapter'].append(q_id)
        
        # Check 3: Bloom's level
        if not q.get('bloomsLevel') or q.get('bloomsLevel') == 'Unknown':
            issues['missing_blooms'].append(q_id)
        
        # Check 4: Difficulty
        if not q.get('difficulty') or q.get('difficulty') not in ['Easy', 'Medium', 'Hard']:
            issues['missing_difficulty'].append(q_id)
        
        # Check 5: Answer
        if not q.get('correctAnswer') or len(str(q.get('correctAnswer'))) < 2:
            issues['missing_answer'].append(q_id)
        
        # Check 6: Explanation
        if not q.get('explanation') or len(q.get('explanation', '')) < 30:
            issues['missing_explanation'].append(q_id)
        
        # Check 7: Text length
        if len(q.get('text', '')) < 30:
            issues['short_text'].append(q_id)
        
        # Check 8: Options for MCQ/AR
        if q.get('type') in ['MCQ', 'AR']:
            options = q.get('options', [])
            if len(options) != 4:
                issues['wrong_options'].append(f"{q_id} ({len(options)} options)")
    
    # Print issues
    total_issues = sum(len(v) for v in issues.values())
    
    for issue_type, question_list in issues.items():
        if question_list:
            issue_name = issue_type.replace('_', ' ').title()
            print(f"\n❌ {issue_name}: {len(question_list)}")
            for q_id in question_list[:3]:  # Show first 3
                print(f"   - {q_id}")
            if len(question_list) > 3:
                print(f"   ... and {len(question_list)-3} more")
    
    if total_issues == 0:
        print("\n✅ No quality issues found!")
    
    # Chapter coverage
    print(f"\n📚 CHAPTER COVERAGE")
    print("-"*80)
    
    chapter_counts = {}
    for q in all_questions:
        ch = q.get('chapter', 'Unknown')
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
    
    covered_chapters = len([ch for ch in chapter_counts if ch != 'Unknown'])
    expected_chapters = 14  # CBSE Class 10 Math
    
    for chapter, count in sorted(chapter_counts.items()):
        print(f"  {chapter:<45} {count} questions")
    
    print(f"\nChapters Covered: {covered_chapters}/{expected_chapters}")
    
    # FINAL VERDICT
    print(f"\n{'='*80}")
    print("🎯 FINAL VERDICT")
    print("="*80)
    
    # Scoring
    score = 100
    
    # Deduct for issues
    score -= len(issues['mock_questions']) * 10  # -10 per mock
    score -= len(issues['missing_chapter']) * 5   # -5 per missing chapter
    score -= len(issues['missing_blooms']) * 3    # -3 per missing bloom's
    score -= len(issues['missing_difficulty']) * 3
    score -= len(issues['missing_answer']) * 8    # -8 per missing answer
    score -= len(issues['missing_explanation']) * 2
    score -= len(issues['short_text']) * 5
    score -= len(issues['wrong_options']) * 4
    
    # Deduct for chapter coverage
    coverage_penalty = (expected_chapters - covered_chapters) * 3
    score -= coverage_penalty
    
    score = max(0, score)
    
    print(f"Quality Score: {score}/100")
    print(f"Total Issues: {total_issues}")
    print(f"Chapter Coverage: {covered_chapters}/{expected_chapters}")
    
    # Decision
    if score >= 85 and len(issues['mock_questions']) == 0:
        decision = "✅ PASS - Good quality, can proceed"
        status = "APPROVED"
    elif score >= 70:
        decision = "⚠️ CONDITIONAL PASS - Has issues but usable"
        status = "NEEDS_FIXES"
    else:
        decision = "❌ FAIL - Too many issues, regenerate required"
        status = "REJECTED"
    
    print(f"\nDecision: {decision}")
    print("="*80)
    
    # Save report
    report = {
        'status': status,
        'score': score,
        'total_questions': len(all_questions),
        'total_issues': total_issues,
        'chapters_covered': covered_chapters,
        'chapters_expected': expected_chapters,
        'issues': {k: len(v) for k, v in issues.items()},
        'decision': decision
    }
    
    with open('exam_quality_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: exam_quality_report.json\n")
    
    return status, score

if __name__ == '__main__':
    exam_path = sys.argv[1] if len(sys.argv) > 1 else 'latest_generated_board_exam.json'
    
    if not Path(exam_path).exists():
        print(f"❌ Error: File not found: {exam_path}")
        sys.exit(1)
    
    status, score = inspect_exam_quality(exam_path)
    
    # Exit code for automation
    sys.exit(0 if status == "APPROVED" else 1)
