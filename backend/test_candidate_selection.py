import os
import sys
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from services.session_manager import session_manager
from services.candidate_profile_service import candidate_profile_service
from services.interview_orchestrator import interview_orchestrator
from models.interview import CandidateEvidenceAnalysis
from models.strategy import StrategyDecision, StrategyAction, DifficultyLevel
from models.question_generator import GeneratedQuestion

client = TestClient(app)


def test_list_candidates():
    """1, 2, 12. GET /api/candidates returns 200, is non-empty, and contains eligibility info."""
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert len(data["candidates"]) > 0

    first = data["candidates"][0]
    assert "candidateId" in first
    assert "name" in first
    assert "eligible" in first
    assert isinstance(first["eligible"], bool)


def test_candidate_ids_unique():
    """3. Candidate IDs returned by /api/candidates are unique."""
    response = client.get("/api/candidates")
    assert response.status_code == 200
    data = response.json()
    ids = [c["candidateId"] for c in data["candidates"]]
    assert len(ids) == len(set(ids))


def test_valid_candidate_lookup():
    """4. CAND-001 can be resolved through CandidateProfileService."""
    candidate = candidate_profile_service.get_candidate("CAND-001")
    assert candidate is not None
    assert candidate["member"]["id"] == "CAND-001"
    assert candidate["member"]["name"] == "Sarah Johnson"


def test_invalid_candidate_404():
    """5. Invalid candidateId returns 404."""
    payload = {
        "sessionId": "session-invalid-id-test",
        "candidateId": "DOES-NOT-EXIST"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("services.interview_orchestrator.interview_orchestrator.question_generator.generate")
def test_valid_candidate_starts_interview(mock_qgen):
    """6, 7, 8, 9. Valid candidateId creates session, plan, reaches start_interview(), and returns first question."""
    session_manager.clear_all()

    # Mock QGen
    mock_generated_q = GeneratedQuestion(
        question_id="q-mock-start",
        question="Can you explain how RAG pipelines handle document retrieval at scale?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe"
    )
    mock_qgen.return_value = mock_generated_q

    payload = {
        "sessionId": "session-selection-test-1",
        "candidateId": "CAND-001"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["done"] is False
    assert data["reply"] == "Can you explain how RAG pipelines handle document retrieval at scale?"

    # Verify session and plan
    assert session_manager.session_exists("session-selection-test-1")
    session = session_manager.get_session("session-selection-test-1")
    assert session["interview_state"].interview_plan is not None
    assert len(session["interview_state"].interview_plan.topic_plans) > 0
    assert session["interview_state"].question_count == 1
    assert session["interview_state"].current_question == "Can you explain how RAG pipelines handle document retrieval at scale?"


def test_knowledge_model_starts_unknown():
    """10. CandidateKnowledgeModel starts with UNKNOWN understanding for all objectives and zero evidence items."""
    session_manager.clear_all()
    session_manager.create_session("session-knowledge-test", candidate_profile_service.get_candidate("CAND-001"))
    
    session = session_manager.get_session("session-knowledge-test")
    km = session["knowledge_model"]
    ledger = session["evidence_ledger"]
    
    assert len(ledger.items) == 0
    
    # Assert all topics and objectives are UNKNOWN
    for day_num, topic_k in km.topics.items():
        assert topic_k.understanding_level == "UNKNOWN"
        for obj_id, obj_k in topic_k.objectives.items():
            assert obj_k.understanding_level == "UNKNOWN"
            assert len(obj_k.evidence_ids) == 0


@patch("services.interview_orchestrator.interview_orchestrator.answer_analyzer.analyze_with_memory")
@patch("services.interview_orchestrator.interview_orchestrator.question_generator.generate")
def test_candidate_selection_then_answer(mock_qgen, mock_analyzer):
    """11. Candidate selection -> first question -> candidate answer -> next question works successfully."""
    session_manager.clear_all()

    # Mock QGen
    mock_q1 = GeneratedQuestion(
        question_id="q-mock-1",
        question="Can you explain how RAG pipelines handle document retrieval at scale?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe"
    )
    mock_q2 = GeneratedQuestion(
        question_id="q-mock-2",
        question="How would you handle chunk sizes in a vector database?",
        target_day=21,
        target_objective="day-21-obj-1",
        difficulty=DifficultyLevel.HARD,
        intent="deepen_rag"
    )
    mock_qgen.side_effect = [mock_q1, mock_q2]

    # Mock Analyzer
    mock_analysis = CandidateEvidenceAnalysis(
        curriculum_day=21,
        topic="RAG",
        understanding_assessment="HIGH",
        assessment_type="supports_understanding",
        confidence=0.9,
        strengths=["Good retrieval grasp"],
        gaps=[],
        evidence_text="Retrieved context properly.",
        candidate_claim="RAG uses retrieval",
        follow_up_recommended=False
    )
    mock_analyzer.return_value = mock_analysis

    # 1. Start interview
    payload1 = {
        "sessionId": "session-full-flow-1",
        "candidateId": "CAND-001"
    }
    resp1 = client.post("/api/interview", json=payload1)
    assert resp1.status_code == 200
    assert resp1.json()["reply"] == "Can you explain how RAG pipelines handle document retrieval at scale?"

    # 2. Submit answer
    payload2 = {
        "sessionId": "session-full-flow-1",
        "message": "I retrieve document chunks using Cosine similarity."
    }
    resp2 = client.post("/api/interview", json=payload2)
    assert resp2.status_code == 200
    assert resp2.json()["reply"] == "How would you handle chunk sizes in a vector database?"
    assert resp2.json()["done"] is False


def test_ineligible_candidate_fails():
    """13. An ineligible candidate (empty completed days) cannot start an interview."""
    session_manager.clear_all()

    # Create a mock candidate with no completed days
    ineligible_candidate = {
        "member": {
            "id": "CAND-INELIGIBLE",
            "name": "No Progress",
            "jobRole": "CS Student",
            "yearsExperience": 0,
            "education": "None",
            "status": "IN_PROGRESS"
        },
        "missions": [],  # no completed missions
        "signals": {"commitDays": 0, "missionsCompleted": 0, "missionsFirstTry": 0}
    }

    # Pass the ineligible candidate dict
    payload = {
        "sessionId": "session-ineligible-test",
        "candidate": ineligible_candidate
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 400
    assert "not eligible" in response.json()["detail"].lower()
    
    # Assert no session remains active
    assert not session_manager.session_exists("session-ineligible-test")


@patch("services.interview_orchestrator.interview_orchestrator.question_generator.generate")
def test_backward_compatible_candidate_object(mock_qgen):
    """14. Existing candidate-object initialization path continues to function."""
    session_manager.clear_all()

    mock_generated_q = GeneratedQuestion(
        question_id="q-compat",
        question="What is prompt injection?",
        target_day=12,
        target_objective="day-12-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe"
    )
    mock_qgen.return_value = mock_generated_q

    cand_profile = candidate_profile_service.get_candidate("CAND-001")
    payload = {
        "sessionId": "session-compat-test",
        "candidate": cand_profile
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 200
    assert response.json()["reply"] == "What is prompt injection?"
    assert session_manager.session_exists("session-compat-test")


def test_debug_endpoint_not_found():
    """Verify debug session endpoint returns 404 for a nonexistent session."""
    response = client.get("/api/debug/session/session-nonexistent-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("services.interview_orchestrator.interview_orchestrator.question_generator.generate")
def test_debug_endpoint_success(mock_qgen):
    """Verify debug session endpoint returns correct metrics for an active session."""
    session_manager.clear_all()

    mock_generated_q = GeneratedQuestion(
        question_id="q-mock-start",
        question="Can you explain how RAG pipelines handle document retrieval at scale?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe"
    )
    mock_qgen.return_value = mock_generated_q

    payload = {
        "sessionId": "session-debug-test-1",
        "candidateId": "CAND-001"
    }
    client.post("/api/interview", json=payload)

    response = client.get("/api/debug/session/session-debug-test-1")
    assert response.status_code == 200
    data = response.json()
    assert data["session_exists"] is True
    assert data["session_id"] == "session-debug-test-1"
    assert data["candidate_id"] == "CAND-001"
    assert data["question_count"] == 1
    assert data["current_turn"] == 1  # start_interview adds 1 assistant message
    assert data["done"] is False
    assert data["current_question"] == "Can you explain how RAG pipelines handle document retrieval at scale?"
    assert data["current_question_meta"]["question_id"] == "q-mock-start"
    assert data["evidence_count"] == 0
    assert data["interview_completed"] is False
