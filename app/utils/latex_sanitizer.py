
"""
LaTeX Sanitization Module for PDF Generation
============================================
Add this to your pdf_generator.py or as a separate module
"""

import re
import json
from copy import deepcopy

def sanitize_latex_for_pdf(text):
    """
    Convert LaTeX mathematical notation to Unicode/plain text for PDF rendering.

    Handles:
    - Fractions: $\frac{a}{b}$ → (a/b)
    - Superscripts: x^2 → x²
    - Greek letters: \alpha → α
    - Math symbols: \times → ×

    Args:
        text (str): Text containing LaTeX notation

    Returns:
        str: Text with LaTeX converted to Unicode/plain text
    """
    if not text or not isinstance(text, str):
        return text

    # Store original for debugging
    original_text = text

    # 1. Convert fractions with $ delimiters: $\frac{a}{b}$ → (a/b)
    text = re.sub(r'\$\\frac\{([^}]+)\}\{([^}]+)\}\$', r'(\1/\2)', text)

    # 2. Convert fractions without $ delimiters: \frac{a}{b} → (a/b)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1/\2)', text)

    # 3. Convert superscripts: 2^m → 2ᵐ, x^2 → x²
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
        'i': 'ⁱ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ',
        'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ'
    }

    def replace_superscript(match):
        base = match.group(1)
        exp = match.group(2)

        # Handle multi-digit exponents
        if len(exp) > 1:
            return f"{base}^({exp})"

        if exp in superscript_map:
            return base + superscript_map[exp]
        return f"{base}^{exp}"

    # Match patterns like: x^2, 2^m, 5^5
    text = re.sub(r'([a-zA-Z0-9])\^([0-9a-zA-Z])', replace_superscript, text)

    # 4. Convert subscripts: x_1 → x₁
    subscript_map = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'n': 'ₙ', 'o': 'ₒ',
        'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'x': 'ₓ'
    }

    def replace_subscript(match):
        base = match.group(1)
        sub = match.group(2)
        if sub in subscript_map:
            return base + subscript_map[sub]
        return f"{base}_{sub}"

    text = re.sub(r'([a-zA-Z])_([0-9a-zA-Z])', replace_subscript, text)

    # 5. Replace Greek letters
    greek_replacements = {
        '\\alpha': 'α',
        '\\beta': 'β',
        '\\gamma': 'γ',
        '\\delta': 'δ',
        '\\epsilon': 'ε',
        '\\theta': 'θ',
        '\\lambda': 'λ',
        '\\mu': 'μ',
        '\\pi': 'π',
        '\\sigma': 'σ',
        '\\phi': 'φ',
        '\\omega': 'ω',
        '\\Delta': 'Δ',
        '\\Theta': 'Θ',
    }

    for latex_cmd, unicode_char in greek_replacements.items():
        text = text.replace(latex_cmd, unicode_char)

    # 6. Replace math operators and symbols
    symbol_replacements = {
        '\\times': '×',
        '\\cdot': '·',
        '\\div': '÷',
        '\\pm': '±',
        '\\neq': '≠',
        '\\leq': '≤',
        '\\geq': '≥',
        '\\approx': '≈',
        '\\equiv': '≡',
        '\\sqrt': '√',
        '\\infty': '∞',
        '\\circ': '°',
        '\\angle': '∠',
        '\\triangle': '△',
        '\\parallel': '∥',
        '\\perp': '⊥',
    }

    for latex_cmd, unicode_char in symbol_replacements.items():
        text = text.replace(latex_cmd, unicode_char)

    # 7. Remove LaTeX delimiters
    text = text.replace('\\(', '')
    text = text.replace('\\)', '')
    text = text.replace('\\[', '')
    text = text.replace('\\]', '')

    # 8. Remove all remaining $ signs
    text = text.replace('$', '')

    # 9. Clean up excessive backslashes
    text = text.replace('\\', '')

    return text


def preprocess_exam_json(exam_data):
    """
    Apply LaTeX sanitization to entire exam JSON structure.

    Args:
        exam_data (dict): Exam JSON with LaTeX notation

    Returns:
        dict: Exam JSON with sanitized text (LaTeX → Unicode/plain text)
    """
    # Deep copy to avoid modifying original
    exam_copy = deepcopy(exam_data)

    for section_id, section_data in exam_copy['sections'].items():
        # Sanitize section name
        if 'name' in section_data:
            section_data['name'] = sanitize_latex_for_pdf(section_data['name'])

        for question in section_data['questions']:
            # Sanitize question text
            if 'text' in question:
                question['text'] = sanitize_latex_for_pdf(question['text'])

            # Sanitize options
            if 'options' in question and question['options']:
                question['options'] = [
                    sanitize_latex_for_pdf(opt) if opt else opt
                    for opt in question['options']
                ]

            # Sanitize correctAnswer
            if 'correctAnswer' in question:
                question['correctAnswer'] = sanitize_latex_for_pdf(
                    question['correctAnswer']
                )

            # Sanitize explanation
            if 'explanation' in question:
                question['explanation'] = sanitize_latex_for_pdf(
                    question['explanation']
                )

            # Sanitize keySteps
            if 'keySteps' in question and question['keySteps']:
                question['keySteps'] = [
                    sanitize_latex_for_pdf(step) if step else step
                    for step in question['keySteps']
                ]

    return exam_copy


# ============================================================================
# INTEGRATION EXAMPLES
# ============================================================================

def test_sanitization():
    """Test the sanitization with sample LaTeX strings"""

    test_cases = [
        ("$\\frac{17}{6}$", "(17/6)"),
        ("$2^m \\times 5^n$", "2ᵐ × 5ⁿ"),
        ("\\alpha + \\beta = 7", "α + β = 7"),
        ("$\\sqrt{119}$ cm", "√119 cm"),
        ("angle of $60^\\circ$", "angle of 60°"),
    ]

    print("\n" + "="*70)
    print("TESTING LATEX SANITIZATION")
    print("="*70)

    all_passed = True
    for original, expected in test_cases:
        result = sanitize_latex_for_pdf(original)
        passed = result == expected
        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"\n{status}")
        print(f"  Input:    {original}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")

        if not passed:
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - CHECK IMPLEMENTATION")
    print("="*70)


if __name__ == "__main__":
    # Run tests
    test_sanitization()
