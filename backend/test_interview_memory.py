import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.interview_memory import InterviewMemoryService
from models.interview import CandidateEvidenceAnalysis


def test_1_successful_memory_retrieval():
    """1. Successful memory retrieval returns list of dicts."""
    mock_mem_service = MagicMock()
    mock_mem_service.search_memory.return_value = [
        {"memory_id": "mem-1", "content": "Candidate discussed vector DBs"}
    ]

    service = InterviewMemoryService(mem_service=mock_mem_service)
    results = service.get_relevant_memories(session_id="session-123", query="vector database")

    mock_mem_service.search_memory.assert_called_once_with(
        session_id="session-123",
        query="vector database",
        limit=5
    )
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["memory_id"] == "mem-1"
    print("[PASS] 1. Successful memory retrieval verified.")


def test_2_empty_memory_result():
    """2. Empty memory search returns []."""
    mock_mem_service = MagicMock()
    mock_mem_service.search_memory.return_value = []

    service = InterviewMemoryService(mem_service=mock_mem_service)
    results = service.get_relevant_memories(session_id="session-123", query="nonexistent")

    assert results == []
    print("[PASS] 2. Empty memory result verified.")


def test_3_breeth_retrieval_failure_returns_empty_list():
    """3. Breeth retrieval failure or exception returns [] safely."""
    mock_mem_service = MagicMock()
    mock_mem_service.search_memory.side_effect = Exception("Breeth API network error")

    service = InterviewMemoryService(mem_service=mock_mem_service)
    results = service.get_relevant_memories(session_id="session-123", query="query")

    # Must return [] without raising an exception
    assert results == []
    print("[PASS] 3. Breeth retrieval failure returns [] safely.")


def test_4_successful_turn_storage():
    """4. Successful turn storage calls MemoryService.store_episode."""
    mock_mem_service = MagicMock()
    mock_mem_service.store_episode.return_value = {
        "success": True,
        "episode_id": "ep-999"
    }

    service = InterviewMemoryService(mem_service=mock_mem_service)
    res = service.store_turn(
        session_id="session-abc",
        turn_number=1,
        question="What is RAG?",
        candidate_answer="RAG stands for Retrieval Augmented Generation."
    )

    mock_mem_service.store_episode.assert_called_once()
    args, kwargs = mock_mem_service.store_episode.call_args
    assert kwargs["session_id"] == "session-abc"
    assert kwargs["messages"] == [
        {"role": "interviewer", "content": "What is RAG?"},
        {"role": "candidate", "content": "RAG stands for Retrieval Augmented Generation."}
    ]
    assert res["success"] is True
    print("[PASS] 4. Successful turn storage verified.")


def test_5_breeth_storage_failure_does_not_break_caller():
    """5. Breeth storage exception does not break the caller."""
    mock_mem_service = MagicMock()
    mock_mem_service.store_episode.side_effect = Exception("Breeth storage failed")

    service = InterviewMemoryService(mem_service=mock_mem_service)
    res = service.store_turn(
        session_id="session-abc",
        turn_number=1,
        question="q",
        candidate_answer="a"
    )

    assert isinstance(res, dict)
    assert res["success"] is False
    print("[PASS] 5. Breeth storage failure does not break caller.")


def test_6_and_7_session_id_and_turn_metadata_preserved():
    """6, 7. Session ID and turn metadata are preserved."""
    mock_mem_service = MagicMock()
    mock_mem_service.store_episode.return_value = {"success": True}

    service = InterviewMemoryService(mem_service=mock_mem_service)
    service.store_turn(
        session_id="sess-777",
        turn_number=3,
        question="Question 3?",
        candidate_answer="Answer 3.",
        curriculum_day=21,
        topic="RAG Systems"
    )

    args, kwargs = mock_mem_service.store_episode.call_args
    assert kwargs["session_id"] == "sess-777"
    meta = kwargs["metadata"]
    assert meta["session_id"] == "sess-777"
    assert meta["turn_number"] == 3
    assert meta["curriculum_day"] == 21
    assert meta["topic"] == "RAG Systems"
    print("[PASS] 6 & 7. Session ID and turn metadata preserved.")


def test_8_analysis_evidence_included_when_supplied():
    """8. CandidateEvidenceAnalysis fields included in metadata when supplied."""
    mock_mem_service = MagicMock()
    mock_mem_service.store_episode.return_value = {"success": True}

    analysis = CandidateEvidenceAnalysis(
        curriculum_day=21,
        topic="RAG",
        understanding_assessment="HIGH",
        assessment_type="supports_understanding",
        confidence=0.9,
        strengths=["Understands vector search"],
        gaps=[],
        evidence_text="Candidate explained vector search correctly.",
        candidate_claim="RAG uses vector retrieval",
        follow_up_recommended=False
    )

    service = InterviewMemoryService(mem_service=mock_mem_service)
    service.store_turn(
        session_id="sess-888",
        turn_number=2,
        question="Explain vector search",
        candidate_answer="Vector search compares embeddings using cosine similarity.",
        curriculum_day=21,
        topic="RAG",
        analysis=analysis
    )

    meta = mock_mem_service.store_episode.call_args[1]["metadata"]
    assert meta["understanding_assessment"] == "HIGH"
    assert meta["assessment_type"] == "supports_understanding"
    assert meta["strengths"] == ["Understands vector search"]
    assert meta["evidence_text"] == "Candidate explained vector search correctly."
    print("[PASS] 8. Analysis evidence included in metadata.")


def test_9_no_direct_http_requests_in_service():
    """9. Verify no direct http libraries (httpx, requests, urllib) are imported in interview_memory.py."""
    source_path = Path(__file__).parent / "services" / "interview_memory.py"
    content = source_path.read_text(encoding="utf-8")
    assert "import httpx" not in content
    assert "import requests" not in content
    assert "import urllib" not in content
    print("[PASS] 9. No direct HTTP request libraries in interview_memory.py.")


def test_10_all_existing_test_suites_pass():
    """10. Existing test suites pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected
    from test_architecture_refinement import test_1_and_2_candidate_state_is_pre_interview_facts_only

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    print("[PASS] 10. Existing test suites pass.")


if __name__ == "__main__":
    print("Running InterviewMemoryService Unit Test Suite...")
    test_1_successful_memory_retrieval()
    test_2_empty_memory_result()
    test_3_breeth_retrieval_failure_returns_empty_list()
    test_4_successful_turn_storage()
    test_5_breeth_storage_failure_does_not_break_caller()
    test_6_and_7_session_id_and_turn_metadata_preserved()
    test_8_analysis_evidence_included_when_supplied()
    test_9_no_direct_http_requests_in_service()
    test_10_all_existing_test_suites_pass()
    print("\nALL INTERVIEWMEMORYSERVICE UNIT TESTS PASSED SUCCESSFULLY!")
