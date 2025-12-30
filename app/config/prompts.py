def get_exam_prompt(context: str, blooms_level: str, count: int, difficulty: str) -> str:
    # --- 1. BLOOM'S TAXONOMY LOGIC ---
    blooms_guide = {
        "Remember": "Recall facts and basic concepts. Verbs: define, list, memorize, repeat, state.",
        "Understand": "Explain ideas or concepts. Verbs: classify, describe, discuss, explain, identify, locate.",
        "Apply": "Use information in new situations. Verbs: execute, implement, solve, use, demonstrate, interpret.",
        "Analyze": "Draw connections among ideas. Verbs: differentiate, organize, relate, compare, contrast.",
        "Evaluate": "Justify a stand or decision. Verbs: appraise, argue, defend, judge, select, support.",
        "Create": "Produce new or original work. Verbs: design, assemble, construct, conjecture, develop."
    }
    
    guide = blooms_guide.get(blooms_level, blooms_guide["Remember"])
    
    # Determine marks based on level
    if blooms_level in ["Remember", "Understand"]:
        marks = 1
    elif blooms_level in ["Apply", "Analyze"]:
        marks = 2
    else: # Evaluate, Create
        marks = 3
    
    # --- 2. PROMPT WITH ONE-SHOT EXAMPLE ---
    prompt = f"""
    Role: Expert NCERT Exam Setter for CBSE Board.
    Context: {context}
    
    Task: Create {count} Multiple Choice Questions (MCQs).
    Target Level: {blooms_level} ({guide}).
    Difficulty: {difficulty}.
    
    CRITICAL JSON FORMATTING RULES:
    1. Output MUST be a valid JSON Array.
    2. "options" MUST be a list of 4 separate strings.
    3. Do NOT merge options into one string.
    4. "correctAnswer" must match exactly one of the strings in "options".
    
    ### EXAMPLE JSON OUTPUT (Follow this format exactly):
    [
      {{
        "text": "Which phenomenon causes the twinkling of stars?",
        "type": "MCQ",
        "options": [
           "Reflection of light",
           "Atmospheric refraction",
           "Dispersion of light",
           "Total internal reflection"
        ],
        "correctAnswer": "Atmospheric refraction",
        "explanation": "Stars twinkle due to the atmospheric refraction of starlight as it passes through varying density layers.",
        "bloomsLevel": "{blooms_level}",
        "marks": {marks},
        "difficulty": "{difficulty}",
        "sourcePage": 1,
        "hasLatex": false
      }}
    ]
    
    Generate {count} questions now. Return ONLY JSON.
    """
    return prompt

def get_quiz_prompt(context: str, count: int, difficulty: str) -> str:
    prompt = f"""
    You are an expert tutor creating a self-practice quiz.
    
    CONTEXT:
    {context}
    
    TASK:
    Generate {count} MCQs. Difficulty: {difficulty}.
    
    CRITICAL JSON FORMAT REQUIREMENTS:
    You must return a valid JSON Array where EVERY object has exactly these keys:
    - "text": The question string
    - "type": "MCQ"
    - "options": Array of 4 strings
    - "correctAnswer": String (must match one of the options exactly)
    - "explanation": String (2-3 sentences explaining WHY it is correct)
    - "bloomsLevel": String (e.g. "Apply", "Understand")
    - "difficulty": "{difficulty}"
    
    OUTPUT EXAMPLE:
    [
        {{
            "text": "What is the speed of light?",
            "type": "MCQ",
            "options": ["3x10^8 m/s", "3x10^6 m/s", "300 km/h", "Infinite"],
            "correctAnswer": "3x10^8 m/s",
            "explanation": "Light travels at approximately 300,000 km/s in a vacuum.",
            "bloomsLevel": "Remember",
            "difficulty": "Medium",
            "sourcePage": 150,
            "hasLatex": false
        }}
    ]
    
    Generate {count} questions now:
    """
    return prompt

def get_flashcard_prompt(context: str, count: int) -> str:
    prompt = f"""
    You are an expert tutor creating study flashcards.
    
    CONTEXT:
    {context}
    
    TASK:
    Generate {count} flashcards. Mix these types:
    1. Definition (Term -> Meaning)
    2. Formula (Name -> Equation)
    3. Concept (Question -> Explanation)
    4. Example (Concept -> Real-world example)
    
    CRITICAL JSON FORMAT REQUIREMENTS:
    You must output a JSON Array where EVERY object uses EXACTLY these keys: "type", "front", "back".
    
    Example:
    [
        {{
            "type": "definition",
            "front": "Refraction",
            "back": "The bending of light when passing from one medium to another.",
            "sourcePage": 120,
            "hasLatex": false
        }}
    ]
    
    Generate {count} cards now. Output ONLY valid JSON.
    """
    return prompt

# def get_tutor_prompt(query: str, context: str, history: list, mode: str) -> str:
#     # Build conversation context
#     history_text = ""
#     if history:
#         history_text = "\n**PREVIOUS CONVERSATION:**\n"
#         for msg in history[-3:]:  # Last 3 messages only
#             # Handle Pydantic model access vs dict access
#             role = getattr(msg, 'role', 'user') if hasattr(msg, 'role') else msg.get('role', 'user')
#             text = getattr(msg, 'text', '') if hasattr(msg, 'text') else msg.get('text', '')
#             history_text += f"{role}: {text}\n"

#     role_desc = "You are a helpful, encouraging Tutor."
#     extra_instructions = "Be simple, direct, use analogies."
    
#     if mode == "teacher_sme":
#         role_desc = "You are a Pedagogical Expert assisting a teacher."
#         extra_instructions = """
#         1. Concept Clarification: Explain depth.
#         2. Teaching Strategy: Suggest how to teach it.
#         3. Common Misconceptions: List student pitfalls.
#         """
        
#     prompt = f"""
#     {role_desc}
    
#     {history_text}
    
#     CONTEXT from Textbook:
#     {context}
    
#     USER QUESTION: {query}
    
#     INSTRUCTIONS:
#     1. Answer based ONLY on the context.
#     2. {extra_instructions}
    
#     Answer:
#     """
#     return prompt
def get_tutor_prompt(query: str, context: str, history: list, mode: str) -> str:
    # Build conversation context
    history_text = ""
    if history:
        history_text = "\n**PREVIOUS CONVERSATION:**\n"
        for msg in history[-3:]:  # Last 3 messages only
            # Handle Pydantic model access vs dict access
            role = getattr(msg, 'role', 'user') if hasattr(msg, 'role') else msg.get('role', 'user')
            text = getattr(msg, 'text', '') if hasattr(msg, 'text') else msg.get('text', '')
            history_text += f"{role}: {text}\n"

    # Default Student Mode Configuration
    role_desc = "You are a helpful, encouraging AI Tutor for a student."
    mode_instructions = """
    1. Be simple, direct, and use analogies suitable for a student.
    2. Break down complex concepts into step-by-step explanations.
    3. Encourage the student to ask follow-up questions.
    """
    
    # Teacher SME Mode Override
    if mode == "teacher_sme":
        role_desc = "You are a Pedagogical Expert assisting a teacher."
        mode_instructions = """
    1. Concept Clarification: Explain the concept in depth.
    2. Teaching Strategy: Suggest specific ways to teach this to students.
    3. Common Misconceptions: List pitfalls students often fall into.
    4. Curriculum Context: Mention how this connects to future topics.
        """
        
    prompt = f"""
    {role_desc}
    
    {history_text}
    
    **CONTEXT from Textbook:**
    {context}
    
    **USER QUESTION:** {query}
    
    **INSTRUCTIONS:**
    {mode_instructions}
    
    **CRITICAL GUARDRAILS:**
    1. Answer based **ONLY** on the provided CONTEXT. 
    2. If the context does not contain sufficient information to answer the question, explicitly state: "This topic is not covered in the current chapter context." 
    3. Do NOT hallucinate information not present in the text.
    4. Use LaTeX for all mathematical formulas (e.g., \( E = mc^2 \)).
    
    Answer:
    """
    return prompt