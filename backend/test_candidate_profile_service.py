import os
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from services.candidate_profile_service import candidate_profile_service
from services.session_manager import session_manager
from models.interview import CandidateState

client = TestClient(app)


def test_1_cand001_loads_successfully():
    """1. CAND-001 loads successfully."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    assert isinstance(state, CandidateState)
    print("[PASS] 1. CAND-001 loads successfully.")


def test_2_cand001_correct_id_and_name():
    """2. CAND-001 has the correct candidate ID and name."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    assert state.candidate_id == "CAND-001"
    assert state.name == "Sarah Johnson"
    assert state.job_role == "Senior Data Engineer"
    assert state.years_experience == 9
    assert state.education == "MS Computer Science"
    assert state.status == "COMPLETED"
    print("[PASS] 2. CAND-001 has correct ID and name.")


def test_3_completed_days_parsed_correctly():
    """3. Completed days are parsed correctly (only passed == True)."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    # CAND-001 passed days: [7, 8, 10, 12, 16, 22, 23, 28, 31]
    expected_completed = [7, 8, 10, 12, 16, 22, 23, 28, 31]
    assert state.completed_days == expected_completed
    print("[PASS] 3. Completed days parsed correctly.")


def test_4_skipped_days_parsed_correctly():
    """4. Skipped days are parsed correctly (only skipped == True)."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    # CAND-001 has day 29 skipped
    assert state.skipped_days == [29]
    print("[PASS] 4. Skipped days parsed correctly.")


def test_5_attempts_parsed_correctly():
    """5. Attempts are parsed correctly."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    expected_attempts = {
        7: 1, 8: 1, 10: 2, 12: 4, 16: 1, 22: 2, 23: 2, 28: 3, 31: 1
    }
    assert state.attempts == expected_attempts
    print("[PASS] 5. Attempts parsed correctly.")


def test_6_signals_parsed_correctly():
    """6. Signals are parsed correctly."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    assert state.signals.commitDays == 28
    assert state.signals.missionsCompleted == 30
    assert state.signals.missionsFirstTry == 20
    print("[PASS] 6. Signals parsed correctly.")


def test_7_nonexistent_candidate_raises_error():
    """7. A non-existent candidate ID raises a clear error."""
    raised = False
    try:
        candidate_profile_service.get_candidate("CAND-999")
    except ValueError as e:
        raised = True
        assert "CAND-999" in str(e)
    assert raised, "Expected ValueError was not raised for nonexistent candidate ID CAND-999"
    print("[PASS] 7. Non-existent candidate ID raises ValueError.")


def test_8_candidate_with_skipped_missions_handled():
    """8. A candidate with skipped missions is handled correctly."""
    # CAND-006 has days 27 and 28 skipped
    state = candidate_profile_service.build_candidate_state("CAND-006")
    assert 27 in state.skipped_days
    assert 28 in state.skipped_days
    assert 27 not in state.completed_days
    assert 28 not in state.completed_days
    print("[PASS] 8. Candidate with skipped missions handled correctly.")


def test_9_failed_mission_not_in_completed_days():
    """9. A mission with passed=false is NOT included in completed_days."""
    # CAND-010 has day 8 with passed: false, attempts: 4
    state = candidate_profile_service.build_candidate_state("CAND-010")
    assert 8 not in state.completed_days
    assert 10 not in state.completed_days  # day 10 also passed: false
    assert 8 in state.attempts
    assert state.attempts[8] == 4
    print("[PASS] 9. Mission with passed=false is NOT in completed_days.")


@patch("services.interview_orchestrator.QuestionGenerator")
@patch("services.interview_orchestrator.AnswerAnalyzer")
def test_10_api_interview_behavior_still_works(MockAnalyzerClass, MockQGenClass):
    """10. Existing POST /api/interview behavior still works."""
    session_manager.clear_all()

    # Mock QGen
    mock_qgen = MagicMock()
    from models.question_generator import GeneratedQuestion
    from models.strategy import DifficultyLevel
    mock_qgen.generate.return_value = GeneratedQuestion(
        question_id="q-mock-1",
        question="Can you explain how RAG pipelines handle document retrieval at scale?",
        target_day=21,
        target_objective="day-21-obj-0",
        difficulty=DifficultyLevel.MEDIUM,
        intent="initial_topic_probe",
    )

    # Mock Analyzer
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

    from services.interview_orchestrator import interview_orchestrator
    original_qgen = interview_orchestrator.question_generator
    original_analyzer = interview_orchestrator.answer_analyzer

    interview_orchestrator.question_generator = mock_qgen
    interview_orchestrator.answer_analyzer = mock_analyzer

    try:
        # First request
        payload1 = {
            "sessionId": "session-test-2a",
            "candidate": {
                "member": {
                    "id": "CAND-001",
                    "name": "Sarah Johnson",
                    "jobRole": "Senior Data Engineer"
                }
            }
        }
        resp1 = client.post("/api/interview", json=payload1)
        assert resp1.status_code == 200
        assert resp1.json()["done"] is False
        assert len(resp1.json()["reply"]) > 0

        # Verify candidate_state was created in session_manager
        session = session_manager.get_session("session-test-2a")
        assert session is not None
        assert session["candidate_state"] is not None
        assert session["candidate_state"].candidate_id == "CAND-001"
        assert session["candidate_state"].name == "Sarah Johnson"

        # Subsequent request
        payload2 = {
            "sessionId": "session-test-2a",
            "message": "Hello, I am ready for the technical questions."
        }
        resp2 = client.post("/api/interview", json=payload2)
        assert resp2.status_code == 200
        assert resp2.json()["done"] is False
        assert len(resp2.json()["reply"]) > 0
        print("[PASS] 10. Existing POST /api/interview behavior still works.")
    finally:
        interview_orchestrator.question_generator = original_qgen
        interview_orchestrator.answer_analyzer = original_analyzer


if __name__ == "__main__":
    print("Running STEP 2A Test Suite...")
    test_1_cand001_loads_successfully()
    test_2_cand001_correct_id_and_name()
    test_3_completed_days_parsed_correctly()
    test_4_skipped_days_parsed_correctly()
    test_5_attempts_parsed_correctly()
    test_6_signals_parsed_correctly()
    test_7_nonexistent_candidate_raises_error()
    test_8_candidate_with_skipped_missions_handled()
    test_9_failed_mission_not_in_completed_days()
    test_10_api_interview_behavior_still_works()
    print("\nALL STEP 2A TESTS PASSED SUCCESSFULLY!")
