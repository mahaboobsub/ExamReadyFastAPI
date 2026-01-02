import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

# Use the key from your .env
HEADERS = {"X-Internal-Key": "dev_secret_key_12345"}

def test_health_v2():
    response = client.get("/v2/exam/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_student_practice_exam():
    """Test: Student gets JSON, No Answers, No LLM"""
    payload = {"template_id": "CBSE_10_SCIENCE_BOARD_2025"}
    
    response = client.post("/v2/exam/student/practice", json=payload, headers=HEADERS)
    
    # 1. Success Check
    assert response.status_code == 200
    data = response.json()
    
    # 2. Structure Check
    assert data["mode"] == "practice"
    assert "questions" in data
    assert len(data["questions"]) > 0
    
    # 3. Security Check (No Answers)
    first_q = data["questions"][0]
    assert first_q.get("correctAnswer") is None, "❌ Security Leak: Answer found in student response!"
    assert first_q.get("explanation") is None, "❌ Security Leak: Explanation found in student response!"
    
    # 4. Performance Check
    assert data["generation_method"] == "pre-generated"

def test_teacher_board_exam():
    """Test: Teacher gets PDFs, Full Metadata"""
    payload = {"template_id": "CBSE_10_SCIENCE_BOARD_2025"}
    
    response = client.post("/v2/exam/teacher/board", json=payload, headers=HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    
    # 1. Structure
    assert data["mode"] == "board"
    assert "exam_pdf_url" in data
    assert "answer_key_pdf_url" in data
    
    # 2. PDF Existence Check (Local dev)
    # The URL is /static/pdfs/..., we check if file exists in data/pdfs/
    pdf_name = data["exam_pdf_url"].split("/")[-1]
    assert os.path.exists(f"data/pdfs/{pdf_name}"), "❌ Exam PDF file not found on disk"

def test_teacher_custom_exam_caching():
    """Test: First request hits DB, Second request hits Cache"""
    payload = {
        "template_id": "CBSE_10_SCIENCE_BOARD_2025",
        "chapters": ["Chemical Reactions and Equations"],
        "chapter_weightage": {"Chemical Reactions and Equations": 100},
        "difficulty": "Medium"
    }
    
    # Request 1 (Computation)
    resp1 = client.post("/v2/exam/teacher/custom", json=payload, headers=HEADERS)
    assert resp1.status_code == 200
    assert resp1.json()["generation_method"] in ["pre-generated", "real-time"]
    
    # Request 2 (Cache)
    resp2 = client.post("/v2/exam/teacher/custom", json=payload, headers=HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["generation_method"] == "cached", "❌ Caching failed!"

def test_validation_errors():
    """Test: Invalid weightage sum"""
    payload = {
        "template_id": "CBSE_10_SCIENCE_BOARD_2025",
        "chapters": ["Chemical Reactions and Equations"],
        "chapter_weightage": {"Chemical Reactions and Equations": 90}, # Sums to 90 (Invalid)
        "difficulty": "Medium"
    }
    
    response = client.post("/v2/exam/teacher/custom", json=payload, headers=HEADERS)
    assert response.status_code == 422 # Unprocessable Entity