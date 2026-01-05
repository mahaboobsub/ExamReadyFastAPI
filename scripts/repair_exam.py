import json
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_exam_generator import LLMExamGenerator

async def repair_exam(file_path):
    print(f"🔧 Repairing {file_path}...")
    path = Path(file_path)
    if not path.exists():
        print("File not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        exam = json.load(f)

    generator = LLMExamGenerator()
    # Ensure Gemini is ready (lazy init Qdrant not needed for simple repair, but harmless)
    
    repaired_count = 0
    
    for section_name, section in exam.get("sections", {}).items():
        for q in section.get("questions", []):
            needs_fix = False
            missing_fields = []
            
            # Check Answer
            if not q.get("correctAnswer") or str(q.get("correctAnswer")).strip() == "":
                missing_fields.append("correctAnswer")
                needs_fix = True
                
            # Check Explanation
            if not q.get("explanation") or str(q.get("explanation")).strip() == "":
                missing_fields.append("explanation")
                needs_fix = True
                
            if needs_fix:
                print(f"  Fixing Q: {q.get('text')[:40]}... Missing: {missing_fields}")
                
                # Ask LLM to solve
                prompt = f"""
                You are a mathematics teacher. Solve this problem for Class 10 student.
                Provide the missing fields: {', '.join(missing_fields)}.
                
                Question: {q.get('text')}
                Options (if any): {q.get('options')}
                Type: {q.get('type')}
                
                Return JSON only: {{ "correctAnswer": "...", "explanation": "..." }}
                """
                
                try:
                    response = await generator.gemini.generate(prompt)
                    # Clean markdown
                    cleaned = response.replace("```json", "").replace("```", "").strip()
                    # Find first { and last }
                    start = cleaned.find("{")
                    end = cleaned.rfind("}")
                    
                    if start != -1 and end != -1:
                        json_str = cleaned[start:end+1]
                        import json
                        fix_data = json.loads(json_str)
                        
                        if "correctAnswer" in missing_fields and "correctAnswer" in fix_data:
                            q["correctAnswer"] = fix_data["correctAnswer"]
                        if "explanation" in missing_fields and "explanation" in fix_data:
                            q["explanation"] = fix_data["explanation"]
                        repaired_count += 1
                        print("    ✅ Fixed.")
                    else:
                        print(f"    ❌ No JSON found in response.")
                except Exception as e:
                    print(f"    ❌ Error: {e} | Response: {response[:100]}")
                    
    if repaired_count > 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(exam, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved repaired file ({repaired_count} fixes).")
    else:
        print("✨ No repairs needed (or failed).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repair_exam.py <json_file>")
    else:
        asyncio.run(repair_exam(sys.argv[1]))
