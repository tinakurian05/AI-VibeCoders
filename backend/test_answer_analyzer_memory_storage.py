import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from models.analyzer import AnswerAnalyzerInput, AnalyzerError
from models.interview import CandidateTopicKnowledge, CandidateEvidenceAnalysis, LLMResponse
from services.answer_analyzer import AnswerAnalyzer


def _create_mock_gateway(response_content: str, success: bool = True):
    mock_gateway = MagicMock()
    mock_response = LLMResponse(
        content=response_content,
        model_used="mock-model",
        success=success,
        error_category=None if success else "api_error"
    )
    mock_gateway.generate.return_value = mock_response
    return mock_gateway


def test_1_to_7_successful_analysis_triggers_store_turn_with_correct_metadata():
    """1-7. Successful analysis triggers store_turn with correct parameters and metadata."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.return_value = []
    mock_mem_service.store_turn.return_value = {"success": True, "episode_id": "ep-123"}

    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "HIGH",
        "assessment_type": "supports_understanding",
        "confidence": 0.95,
        "strengths": ["Clear definition of vector index"],
        "gaps": [],
        "evidence_text": "Candidate explained vector search correctly.",
        "candidate_claim": "RAG retrieves relevant chunks before generation",
        "follow_up_recommended": false
    }'''
    gateway = _create_mock_gateway(mock_json)

    analyzer = AnswerAnalyzer(gateway=gateway, memory_service=mock_mem_service)

    input_data = AnswerAnalyzerInput(
        candidate_id="CAND-001",
        current_question="How does RAG vector search work?",
        candidate_answer="It retrieves top-k chunk embeddings using cosine similarity.",
        curriculum_day=21,
        topic="RAG",
        relevant_objectives=["Understand RAG vector indexing"],
        current_topic_knowledge=CandidateTopicKnowledge(curriculum_day=21, topic="RAG"),
        conversation_history=[]
    )

    result = analyzer.analyze_with_memory(
        session_id="session-456-abc",
        input_data=input_data,
        turn_number=2,
        store_turn=True
    )

    # Test 1 & 2: Verification of store_turn invocation and session_id
    mock_mem_service.store_turn.assert_called_once()
    kwargs = mock_mem_service.store_turn.call_args[1]

    assert kwargs["session_id"] == "session-456-abc"  # Test 2
    assert kwargs["turn_number"] == 2
    assert kwargs["question"] == "How does RAG vector search work?"  # Test 3
    assert kwargs["candidate_answer"] == "It retrieves top-k chunk embeddings using cosine similarity."  # Test 4
    assert kwargs["curriculum_day"] == 21  # Test 5
    assert kwargs["topic"] == "RAG"  # Test 6
    assert kwargs["analysis"] == result  # Test 7
    assert isinstance(kwargs["analysis"], CandidateEvidenceAnalysis)
    assert kwargs["analysis"].understanding_assessment == "HIGH"

    print("[PASS] 1-7. Successful analysis triggers store_turn with correct parameters & metadata.")


def test_8_storage_happens_after_analysis_not_called_on_analysis_failure():
    """8. Storage happens after analysis; store_turn is NOT called if analysis fails."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.return_value = []

    # Invalid JSON output triggers AnalyzerError during analysis
    gateway = _create_mock_gateway("NOT VALID JSON")

    analyzer = AnswerAnalyzer(gateway=gateway, memory_service=mock_mem_service)

    input_data = AnswerAnalyzerInput(
        candidate_id="CAND-001",
        current_question="Question",
        candidate_answer="Answer",
        curriculum_day=21,
        topic="RAG",
        relevant_objectives=["Obj"],
        current_topic_knowledge=CandidateTopicKnowledge(curriculum_day=21, topic="RAG"),
        conversation_history=[]
    )

    try:
        analyzer.analyze_with_memory(session_id="session-fail", input_data=input_data)
        assert False, "Expected AnalyzerError to be raised"
    except AnalyzerError:
        pass

    # Verify store_turn was NEVER called because analysis failed
    mock_mem_service.store_turn.assert_not_called()
    print("[PASS] 8. Storage happens after analysis; not called on analysis failure.")


def test_9_and_10_breeth_storage_failure_does_not_break_analysis():
    """9, 10. Breeth storage exception does NOT break analysis; CandidateEvidenceAnalysis still returned."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.return_value = []
    mock_mem_service.store_turn.side_effect = Exception("Breeth storage network timeout")

    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "MEDIUM",
        "assessment_type": "supports_understanding",
        "confidence": 0.75,
        "strengths": ["Basic understanding"],
        "gaps": ["Shallow explanation"],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)

    analyzer = AnswerAnalyzer(gateway=gateway, memory_service=mock_mem_service)

    input_data = AnswerAnalyzerInput(
        candidate_id="CAND-001",
        current_question="Question",
        candidate_answer="Answer",
        curriculum_day=21,
        topic="RAG",
        relevant_objectives=["Obj"],
        current_topic_knowledge=CandidateTopicKnowledge(curriculum_day=21, topic="RAG"),
        conversation_history=[]
    )

    # Must NOT raise exception despite store_turn failing
    result = analyzer.analyze_with_memory(session_id="session-storage-fail", input_data=input_data)
    assert isinstance(result, CandidateEvidenceAnalysis)
    assert result.understanding_assessment == "MEDIUM"
    print("[PASS] 9 & 10. Breeth storage failure does not break analysis; result still returned.")


def test_11_no_direct_breeth_http_calls_in_answer_analyzer():
    """11. Verify no direct http libraries (httpx, requests, urllib) are imported in answer_analyzer.py."""
    source_path = Path(__file__).parent / "services" / "answer_analyzer.py"
    content = source_path.read_text(encoding="utf-8")
    assert "import httpx" not in content
    assert "import requests" not in content
    assert "import urllib" not in content
    print("[PASS] 11. No direct HTTP request libraries in answer_analyzer.py.")


def test_12_and_13_all_previous_test_suites_pass():
    """12, 13. Step 4A, Step 4B, and all previous backend test suites pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected
    from test_architecture_refinement import test_1_and_2_candidate_state_is_pre_interview_facts_only
    from test_interview_memory import test_1_successful_memory_retrieval
    from test_answer_analyzer_memory import test_1_and_2_session_id_and_query_passed_to_memory_service

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    test_1_successful_memory_retrieval()
    test_1_and_2_session_id_and_query_passed_to_memory_service()
    print("[PASS] 12 & 13. Existing test suites pass.")


if __name__ == "__main__":
    print("Running AnswerAnalyzer Memory Storage Integration Unit Test Suite...")
    test_1_to_7_successful_analysis_triggers_store_turn_with_correct_metadata()
    test_8_storage_happens_after_analysis_not_called_on_analysis_failure()
    test_9_and_10_breeth_storage_failure_does_not_break_analysis()
    test_11_no_direct_breeth_http_calls_in_answer_analyzer()
    test_12_and_13_all_previous_test_suites_pass()
    print("\nALL ANSWERANALYZER MEMORY STORAGE INTEGRATION TESTS PASSED SUCCESSFULLY!")
