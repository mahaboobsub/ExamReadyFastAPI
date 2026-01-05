import hashlib
import re
from typing import List, Dict, Set
from difflib import SequenceMatcher

def extract_numbers(text: str) -> Set[str]:
    """Extract all numbers from text for comparison"""
    return set(re.findall(r'\d+\.?\d*', text))

def text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using SequenceMatcher (0.0 to 1.0)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def deduplicate_questions(questions: List[Dict]) -> List[Dict]:
    """
    Smart deduplication:
    1. MD5 Hash (Exact match)
    2. Text similarity with number-awareness
       - If text 90%+ similar but numbers differ → keep both (different problems)
       - If text 95%+ similar and numbers same → duplicate
    """
    unique = []
    seen_hashes = set()
    seen_texts = []  # Store normalized texts for comparison
    
    for q in questions:
        # 1. ID Check
        if not q.get("id"): 
            continue
        
        # 2. Text Hash (Exact match)
        text = q.get("text", "").strip()
        if not text:
            continue
            
        text_lower = text.lower()
        md5 = hashlib.md5(text_lower.encode()).hexdigest()
        
        if md5 in seen_hashes:
            continue
        
        # 3. Similarity check with number-awareness
        is_duplicate = False
        current_numbers = extract_numbers(text)
        
        for seen_text, seen_numbers in seen_texts:
            similarity = text_similarity(text_lower, seen_text)
            
            # High similarity check
            if similarity > 0.90:
                # If numbers are different, it's a different problem - keep it
                if current_numbers != seen_numbers and len(current_numbers) > 0:
                    continue  # Not a duplicate
                
                # If 95%+ similar with same or no numbers, it's a duplicate
                if similarity > 0.95:
                    is_duplicate = True
                    break
        
        if is_duplicate:
            continue
        
        # Not a duplicate - add to unique list
        seen_hashes.add(md5)
        seen_texts.append((text_lower, current_numbers))
        unique.append(q)
    
    return unique