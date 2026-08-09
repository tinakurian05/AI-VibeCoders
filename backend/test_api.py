import json
import os
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from services.session_manager import session_manager
from models.interview import LLMResponse

client = TestClient(app)


def _mock_llm_question_response():
    """Return a mock LLMResponse containing a valid GeneratedQuestion JSON."""
    question_json = json.dumps({
        "question_id": "q-mock-1",
        "question": "Can you explain how RAG pipelines handle document retrieval at scale?",
        "target_day": 21,
        "target_objective": "day-21-obj-0",
        "difficulty": "MEDIUM",
        "intent": "initial_topic_probe",
    })
    return LLMResponse(
        content=question_json,
        model_used="mock-model",
        provider="mock",
        latency_ms=10.0,
        success=True,
    )


def _mock_llm_analysis_response():
    """Return a mock LLMResponse containing a valid CandidateEvidenceAnalysis JSON."""
    analysis_json = json.dumps({
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "MEDIUM",
        "assessment_type": "supports_understanding",
        "confidence": 0.7,
        "strengths": ["Basic understanding"],
        "gaps": ["Lacks depth"],
        "evidence_text": "Candidate showed partial understanding",
        "candidate_claim": "RAG uses retrieval",
        "follow_up_recommended": True,
    })
    return LLMResponse(
        content=analysis_json,
        model_used="mock-model",
        provider="mock",
        latency_ms=10.0,
        success=True,
    )


def _mock_llm_next_question_response():
    """Return a mock LLMResponse for the second question."""
    question_json = json.dumps({
        "question_id": "q-mock-2",
        "question": "How would you handle document chunking for a large corpus?",
        "target_day": 21,
        "target_objective": "day-21-obj-0",
        "difficulty": "MEDIUM",
        "intent": "address_specific_gap",
    })
    return LLMResponse(
        content=question_json,
        model_used="mock-model",
        provider="mock",
        latency_ms=10.0,
        success=True,
    )


def test_health_check():
    """Verify GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {"status": "ok"}, f"Unexpected payload: {response.json()}"
    print("[PASS] GET /health works successfully.")


@patch("services.interview_orchestrator.QuestionGenerator")
def test_create_session(MockQGenClass):
    """Verify POST /api/interview with candidate creates a new session and generates first question."""
    session_manager.clear_all()

    # Mock QuestionGenerator to return a deterministic question
    mock_qgen_instance = MagicMock()
    from models.question_generator import GeneratedQuestion
    from models.strategy import DifficultyLevel
    mock_qgen_instance.generate.return_value = GeneratedQuestion(
        question_id="q-mock-1",
        question="Can you explain how RAG pipelines handle document retrieval at scale?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe",
    )

    # Patch the global orchestrator's question_generator
    from services.interview_orchestrator import interview_orchestrator
    original_qgen = interview_orchestrator.question_generator
    interview_orchestrator.question_generator = mock_qgen_instance

    try:
        payload = {
            "sessionId": "test-session-101",
            "candidate": {
                "member": {
                    "id": "CAND-001",
                    "name": "Sarah Johnson",
                    "jobRole": "Senior Data Engineer"
                }
            }
        }
        response = client.post("/api/interview", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["done"] is False
        assert len(data["reply"]) > 0, "Expected a non-empty reply with a generated question"
        assert session_manager.session_exists("test-session-101")

        # Verify question state was populated
        session = session_manager.get_session("test-session-101")
        interview_state = session["interview_state"]
        assert interview_state.current_question is not None
        assert interview_state.question_count >= 1
        print("[PASS] POST /api/interview with candidate creates session and generates first question.")
    finally:
        interview_orchestrator.question_generator = original_qgen


@patch("services.interview_orchestrator.QuestionGenerator")
def test_subsequent_message(MockQGenClass):
    """Verify POST /api/interview with existing session processes an answer."""
    # Ensure session exists from previous test
    if not session_manager.session_exists("test-session-101"):
        test_create_session(MockQGenClass)

    from services.interview_orchestrator import interview_orchestrator
    original_qgen = interview_orchestrator.question_generator
    original_analyzer = interview_orchestrator.answer_analyzer

    # Mock analyzer
    mock_analyzer = MagicMock()
    from models.interview import CandidateEvidenceAnalysis
    mock_analyzer.analyze_with_memory.return_value = CandidateEvidenceAnalysis(
        curriculum_day=21,
        topic="RAG",
        understanding_assessment="MEDIUM",
        assessment_type="supports_understanding",
        confidence=0.7,
        strengths=["Basic understanding"],
        gaps=["Lacks depth"],
        evidence_text="Candidate showed partial understanding",
        candidate_claim="RAG uses retrieval",
        follow_up_recommended=True,
    )

    # Mock question generator
    mock_qgen = MagicMock()
    from models.question_generator import GeneratedQuestion
    from models.strategy import DifficultyLevel
    mock_qgen.generate.return_value = GeneratedQuestion(
        question_id="q-mock-2",
        question="How would you handle document chunking for a large corpus?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="address_specific_gap",
    )

    interview_orchestrator.answer_analyzer = mock_analyzer
    interview_orchestrator.question_generator = mock_qgen

    try:
        payload = {
            "sessionId": "test-session-101",
            "message": "I have experience with Python and distributed systems.",
        }
        response = client.post("/api/interview", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["done"] is False
        assert len(data["reply"]) > 0, "Expected a non-empty reply with next question"
        print("[PASS] POST /api/interview with existing sessionId + message processes answer successfully.")
    finally:
        interview_orchestrator.question_generator = original_qgen
        interview_orchestrator.answer_analyzer = original_analyzer


def test_nonexistent_session_404():
    """Verify POST /api/interview with new sessionId + message returns 404."""
    payload = {
        "sessionId": "unknown-session-999",
        "message": "Hello?"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    print("[PASS] POST /api/interview with missing sessionId returns 404 as expected.")


def test_empty_session_id_validation():
    """Verify empty sessionId fails validation."""
    payload = {
        "sessionId": "   ",
        "message": "Hello"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code in (400, 422), f"Expected 400 or 422, got {response.status_code}"
    print("[PASS] Empty sessionId validation works as expected.")


if __name__ == "__main__":
    print("Running Step 1 Backend API Tests...")
    test_health_check()
    test_create_session(None)
    test_subsequent_message(None)
    test_nonexistent_session_404()
    test_empty_session_id_validation()
    print("\nALL STEP 1 TESTS PASSED SUCCESSFULLY!")
