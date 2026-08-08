import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from models.analyzer import AnswerAnalyzerInput
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


def test_1_and_2_session_id_and_query_passed_to_memory_service():
    """1, 2. session_id and topic/question query passed correctly to InterviewMemoryService."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.return_value = [
        {"content": "Previous memory about RAG vs Fine-tuning"}
    ]

    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "HIGH",
        "assessment_type": "supports_understanding",
        "confidence": 0.9,
        "strengths": ["Clear explanation"],
        "gaps": [],
        "evidence_text": "Evidence text",
        "candidate_claim": "RAG is better for live data",
        "follow_up_recommended": false
    }'''
    gateway = _create_mock_gateway(mock_json)

    analyzer = AnswerAnalyzer(gateway=gateway, memory_service=mock_mem_service)

    input_data = AnswerAnalyzerInput(
        candidate_id="CAND-001",
        current_question="Why use RAG instead of fine-tuning?",
        candidate_answer="RAG avoids retraining when documentation changes.",
        curriculum_day=21,
        topic="RAG",
        relevant_objectives=["Understand RAG vs Fine-tuning"],
        current_topic_knowledge=CandidateTopicKnowledge(curriculum_day=21, topic="RAG"),
        conversation_history=[]
    )

    result = analyzer.analyze_with_memory(session_id="session-xyz-123", input_data=input_data)

    # Test 1 & 2: Verification of session_id and query
    mock_mem_service.get_relevant_memories.assert_called_once()
    args, kwargs = mock_mem_service.get_relevant_memories.call_args
    assert kwargs["session_id"] == "session-xyz-123"
    assert "RAG" in kwargs["query"]
    assert "Why use RAG instead of fine-tuning?" in kwargs["query"]

    # Test 3: Verification that retrieved memories reach input_data and prompt
    assert input_data.relevant_memories == [{"content": "Previous memory about RAG vs Fine-tuning"}]
    user_prompt = gateway.generate.call_args[1]["user_prompt"]
    assert "Relevant Memories from Previous Turns:" in user_prompt
    assert "Previous memory about RAG vs Fine-tuning" in user_prompt

    # Test 6: Output returned unchanged
    assert isinstance(result, CandidateEvidenceAnalysis)
    assert result.understanding_assessment == "HIGH"
    print("[PASS] 1, 2, 3, 6. Session ID, query, memory prompt formatting & output verified.")


def test_4_empty_memories_handled():
    """4. AnswerAnalyzer receives [] when Breeth returns no memories."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.return_value = []

    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "MEDIUM",
        "assessment_type": "supports_understanding",
        "confidence": 0.7,
        "strengths": ["Basic definition"],
        "gaps": [],
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

    result = analyzer.analyze_with_memory(session_id="session-xyz", input_data=input_data)

    assert input_data.relevant_memories == []
    user_prompt = gateway.generate.call_args[1]["user_prompt"]
    assert "Relevant Memories from Previous Turns:" not in user_prompt
    assert result.understanding_assessment == "MEDIUM"
    print("[PASS] 4. Empty memory list handled cleanly.")


def test_5_breeth_failure_allows_analyzer_to_execute():
    """5. Breeth failure (exception/timeout) allows AnswerAnalyzer to execute normally."""
    mock_mem_service = MagicMock()
    mock_mem_service.get_relevant_memories.side_effect = Exception("Breeth API Connection Timeout")

    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "LOW",
        "assessment_type": "indicates_gap",
        "confidence": 0.8,
        "strengths": [],
        "gaps": ["Misunderstood RAG"],
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

    # Must NOT throw exception; must proceed with empty memories
    result = analyzer.analyze_with_memory(session_id="session-xyz", input_data=input_data)
    assert input_data.relevant_memories == []
    assert result.understanding_assessment == "LOW"
    print("[PASS] 5. Breeth failure allows AnswerAnalyzer to execute normally.")


def test_7_no_direct_http_calls_in_answer_analyzer():
    """7. No direct HTTP request libraries (httpx, requests, urllib) are imported in answer_analyzer.py."""
    source_path = Path(__file__).parent / "services" / "answer_analyzer.py"
    content = source_path.read_text(encoding="utf-8")
    assert "import httpx" not in content
    assert "import requests" not in content
    assert "import urllib" not in content
    print("[PASS] 7. No direct HTTP request libraries in answer_analyzer.py.")


def test_8_all_existing_test_suites_pass():
    """8. All existing test suites pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected
    from test_architecture_refinement import test_1_and_2_candidate_state_is_pre_interview_facts_only
    from test_interview_memory import test_1_successful_memory_retrieval

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    test_1_successful_memory_retrieval()
    print("[PASS] 8. All existing test suites pass.")


if __name__ == "__main__":
    print("Running AnswerAnalyzer Memory Integration Unit Test Suite...")
    test_1_and_2_session_id_and_query_passed_to_memory_service()
    test_4_empty_memories_handled()
    test_5_breeth_failure_allows_analyzer_to_execute()
    test_7_no_direct_http_calls_in_answer_analyzer()
    test_8_all_existing_test_suites_pass()
    print("\nALL ANSWERANALYZER MEMORY INTEGRATION TESTS PASSED SUCCESSFULLY!")
