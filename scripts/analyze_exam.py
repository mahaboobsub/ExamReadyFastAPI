#!/usr/bin/env python3
"""Comprehensive exam analysis for CBSE Class 10 Mathematics."""

import json

with open('full_14_chapter_exam_FINAL.json', 'r', encoding='utf-8') as f:
    exam = json.load(f)

print('='*80)
print('CBSE CLASS 10 MATHEMATICS EXAM ANALYSIS')
print('='*80)

# Collect all questions
all_questions = []
for section_id, section in exam['sections'].items():
    for q in section['questions']:
        q['section'] = section_id
        all_questions.append(q)

# 1. CHAPTER COVERAGE
print('\n1. CHAPTER COVERAGE (14 CBSE Chapters)')
print('-'*60)
chapter_counts = {}
for q in all_questions:
    ch = q.get('chapter', 'Unknown')
    chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

cbse_chapters = [
    'Real Numbers', 'Polynomials', 
    'Pair of Linear Equations in Two Variables', 'Quadratic Equations',
    'Arithmetic Progressions', 'Triangles', 'Coordinate Geometry',
    'Introduction to Trigonometry', 'Applications of Trigonometry',
    'Circles', 'Areas Related to Circles', 'Surface Areas and Volumes',
    'Statistics', 'Probability'
]

covered = 0
for ch in cbse_chapters:
    count = chapter_counts.get(ch, 0)
    status = 'OK' if count > 0 else 'MISSING'
    if count > 0:
        covered += 1
    print(f'  {status} {ch}: {count} questions')

print(f'\nChapters Covered: {covered}/14')

# 2. BLOOM'S TAXONOMY DISTRIBUTION
print('\n2. BLOOMS TAXONOMY DISTRIBUTION')
print('-'*60)
blooms_counts = {}
for q in all_questions:
    bl = q.get('bloomsLevel', 'Unknown')
    blooms_counts[bl] = blooms_counts.get(bl, 0) + 1

for level, count in sorted(blooms_counts.items()):
    pct = count / len(all_questions) * 100
    print(f'  {level}: {count} ({pct:.1f}%)')

# 3. DIFFICULTY DISTRIBUTION
print('\n3. DIFFICULTY DISTRIBUTION')
print('-'*60)
diff_counts = {}
for q in all_questions:
    d = q.get('difficulty', 'Unknown')
    diff_counts[d] = diff_counts.get(d, 0) + 1

for level, count in sorted(diff_counts.items()):
    pct = count / len(all_questions) * 100
    print(f'  {level}: {count} ({pct:.1f}%)')

# 4. QUESTION TYPE DISTRIBUTION
print('\n4. QUESTION TYPE DISTRIBUTION')
print('-'*60)
type_counts = {}
for q in all_questions:
    t = q.get('type', 'Unknown')
    type_counts[t] = type_counts.get(t, 0) + 1

for qtype, count in sorted(type_counts.items()):
    print(f'  {qtype}: {count}')

# 5. SECTION BREAKDOWN
print('\n5. SECTION BREAKDOWN (CBSE Pattern)')
print('-'*60)
for section_id, section in exam['sections'].items():
    qcount = len(section['questions'])
    marks = section.get('marks', 0)
    name = section.get('name', 'Unknown')
    print(f'  Section {section_id}: {name}')
    print(f'     Questions: {qcount}, Marks: {marks}')

# 6. METADATA SUMMARY
print('\n6. METADATA SUMMARY')
print('-'*60)
meta = exam.get('metadata', {})
print(f'  Board: {meta.get("board", "N/A")}')
print(f'  Class: {meta.get("class", "N/A")}')
print(f'  Subject: {meta.get("subject", "N/A")}')
print(f'  Total Questions: {meta.get("totalQuestions", "N/A")}')
print(f'  Total Marks: {meta.get("totalMarks", "N/A")}')
print(f'  Duration: {meta.get("duration", "N/A")} minutes')
print(f'  Generation Method: {meta.get("generationMethod", "N/A")}')

print('\n' + '='*80)
print('EXAM IS READY FOR PDF GENERATION!')
print('='*80)
