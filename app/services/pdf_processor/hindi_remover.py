"""
Hindi Text Removal using Unicode regex
Devanagari Range: U+0900 to U+097F
"""
import re
from typing import Tuple


def contains_hindi(text: str) -> bool:
    """
    Check if text contains Hindi (Devanagari) characters
    
    Args:
        text: Input text to check
        
    Returns:
        True if Hindi characters found, False otherwise
    """
    return bool(re.search(r'[\u0900-\u097F]', text))


def remove_hindi_text(text: str) -> str:
    """
    Remove all Devanagari (Hindi) characters from text
    
    Unicode Ranges:
    - Devanagari: U+0900 to U+097F
    - Devanagari Extended: U+A8E0 to U+A8FF
    - Vedic Extensions: U+1CD0 to U+1CFF
    
    Args:
        text: Input text with mixed Hindi and English
        
    Returns:
        Cleaned text with Hindi removed
        
    Example:
        >>> remove_hindi_text("गणित (मानक) MATHEMATICS (STANDARD)")
        'MATHEMATICS (STANDARD)'
    """
    # Remove main Devanagari block
    text = re.sub(r'[\u0900-\u097F]+', '', text)
    
    # Remove Devanagari Extended
    text = re.sub(r'[\uA8E0-\uA8FF]+', '', text)
    
    # Remove Vedic Extensions
    text = re.sub(r'[\u1CD0-\u1CFF]+', '', text)
    
    # Remove Hindi-specific punctuation (Danda, Double Danda)
    text = re.sub(r'[।॥]', '', text)
    
    # Clean up multiple spaces caused by removal
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up orphaned parentheses/brackets
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\[\s*\]', '', text)
    
    # Clean up multiple hyphens/dashes
    text = re.sub(r'-{2,}', '-', text)
    
    return text.strip()


def remove_hindi_preserve_structure(text: str) -> Tuple[str, int]:
    """
    Remove Hindi while preserving document structure (newlines, paragraphs)
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (cleaned_text, hindi_chars_removed)
    """
    # Count Hindi characters before removal
    hindi_count = len(re.findall(r'[\u0900-\u097F]', text))
    
    # Process line by line to preserve structure
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove Hindi from each line
        cleaned_line = re.sub(r'[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF।॥]+', '', line)
        
        # Clean up spaces within line
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line).strip()
        
        # Keep non-empty lines
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines), hindi_count
