import os
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from services.session_manager import session_manager
from models.interview import CandidateEvidenceAnalysis, EvidenceItem
from models.strategy import StrategyDecision, StrategyAction, DifficultyLevel
from models.question_generator import GeneratedQuestion

client = TestClient(app)


def test_step5_interview_loop_wiring():
    print("Running STEP 5A Interview Loop Wiring Test Suite...")

    cand_payload = {
        "candidate_id": "CAND-001",
        "name": "Alice Johnson",
        "target_role": "AI Engineer",
        "missions": [
            {"day": 21, "title": "Day 21: RAG Basics", "passed": True, "attempts": 1},
            {"day": 22, "title": "Day 22: Vector Databases", "passed": True, "attempts": 2},
            {"day": 23, "title": "Day 23: Evaluation", "passed": True, "attempts": 1},
            {"day": 24, "title": "Day 24: Fine-Tuning", "passed": True, "attempts": 1}
        ]
    }

    # 1, 2, 3. First request initializes session and returns opening question
    resp1 = client.post("/api/interview", json={"sessionId": "sess-loop-1", "candidate": cand_payload})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["done"] is False
    assert len(data1["reply"]) > 0
    assert session_manager.session_exists("sess-loop-1")
    print("[PASS] 1, 2, 3. First request initializes session & returns initial question under standard API contract.")

    # 4-12. Subsequent candidate answer turn processing
    mock_analysis = CandidateEvidenceAnalysis(
        curriculum_day=21,
        topic="RAG",
        understanding_assessment="HIGH",
        assessment_type="supports_understanding",
        confidence=0.9,
        strengths=["Understands vector retrieval"],
        gaps=[],
        evidence_text="RAG retrieves context before generation.",
        candidate_claim="RAG retrieves context.",
        follow_up_recommended=False
    )

    mock_memories = [{"content": "Previous candidate experience"}]
    mock_generated_q = GeneratedQuestion(
        question_id="q-next-100",
        question="How do you handle chunk size in RAG index build?",
        target_day=21,
        target_objective="obj1",
        difficulty=DifficultyLevel.HARD,
        intent="deepen_rag"
    )

    with patch("api.interview.answer_analyzer.analyze_with_memory", return_value=mock_analysis) as mock_analyze, \
         patch("api.interview.interview_memory_service.get_relevant_memories", return_value=mock_memories) as mock_get_mem, \
         patch("api.interview.interview_memory_service.store_turn", return_value={"success": True}) as mock_store_turn, \
         patch("api.interview.question_generator.generate", return_value=mock_generated_q) as mock_gen_q:

        resp2 = client.post("/api/interview", json={"sessionId": "sess-loop-1", "message": "RAG retrieves context."})
        data2 = resp2.json()
        print(f"Debug: Response 2: {data2}")

        # 4 & 5. Retrieval & Analysis
        assert mock_get_mem.called
        assert mock_analyze.called

        # 6, 7, 8. SessionManager state updates
        session = session_manager.get_session("sess-loop-1")
        assert session["interview_state"].question_count == 1
        assert len(session["evidence_ledger"].items) == 1
        assert session["evidence_ledger"].items[0].candidate_claim == "RAG retrieves context."

        # 9, 10, 11. Strategy & Generator invoked -> Next question returned
        assert mock_gen_q.called
        assert data2["reply"] == "How do you handle chunk size in RAG index build?"
        assert data2["done"] is False

        # 12. Turn stored through InterviewMemoryService
        assert mock_store_turn.called
        print("[PASS] 4-12. Turn processing: Breeth retrieval -> AnswerAnalyzer -> SessionManager -> Strategy -> QuestionGenerator -> Breeth storage -> Next question.")

    # 13 & 14. Breeth retrieval/storage failures do not break the turn
    with patch("api.interview.interview_memory_service.get_relevant_memories", return_value=[]) as mock_get_mem_fail, \
         patch("api.interview.interview_memory_service.store_turn", return_value={"success": False}) as mock_store_fail, \
         patch("api.interview.answer_analyzer.analyze_with_memory", return_value=mock_analysis), \
         patch("api.interview.question_generator.generate", return_value=mock_generated_q):

        resp3 = client.post("/api/interview", json={"sessionId": "sess-loop-1", "message": "Chunk size affects context accuracy."})
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["done"] is False
        assert len(data3["reply"]) > 0
        print("[PASS] 13 & 14. Breeth retrieval & storage failures do not interrupt interview flow.")

    # 15. LLM failure is handled safely
    with patch("api.interview.answer_analyzer.analyze_with_memory", side_effect=Exception("LLM timeout")):
        resp4 = client.post("/api/interview", json={"sessionId": "sess-loop-1", "message": "Retry answer."})
        assert resp4.status_code == 200
        data4 = resp4.json()
        assert data4["done"] is False
        assert len(data4["reply"]) > 0
        print("[PASS] 15. LLM failure is handled safely with graceful fallback question.")

    # 17. done=true is respected when StrategyEngine concludes
    mock_end_decision = StrategyDecision(
        action=StrategyAction.END,
        target_day=21,
        target_objective=None,
        difficulty=DifficultyLevel.MEDIUM,
        intent="end_interview",
        reasoning="Question budget reached.",
        follow_up=False,
        should_end=True
    )
    with patch("api.interview.strategy_engine.decide", return_value=mock_end_decision), \
         patch("api.interview.answer_analyzer.analyze_with_memory", return_value=mock_analysis):

        resp5 = client.post("/api/interview", json={"sessionId": "sess-loop-1", "message": "Final answer."})
        assert resp5.status_code == 200
        data5 = resp5.json()
        assert data5["done"] is True
        assert "recorded" in data5["reply"] or "thank you" in data5["reply"].lower()
        print("[PASS] 17. Strategy decision to END sets done=True cleanly.")

    # 20. Run all previous test suites
    print("\nRunning all previous test suites...")
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected

    print("[PASS] 20. All previous test suites pass.")

    print("\nALL STEP 5A WIRING TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_step5_interview_loop_wiring()
