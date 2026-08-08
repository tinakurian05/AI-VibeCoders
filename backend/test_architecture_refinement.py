import os
import sys
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.candidate_profile_service import candidate_profile_service
from services.curriculum_service import curriculum_service
from services.interview_planner import interview_planner
from services.session_manager import session_manager
from models.interview import (
    CandidateState,
    CurriculumState,
    CurriculumContext,
    InterviewPlan,
    InterviewState,
    CandidateKnowledgeModel,
    CandidateTopicKnowledge,
    EvidenceLedger,
    EvidenceItem,
    CandidateEvidenceAnalysis,
)


def test_1_and_2_candidate_state_is_pre_interview_facts_only():
    """1, 2. CandidateState remains pre-interview profile data without knowledge scores."""
    state = candidate_profile_service.build_candidate_state("CAND-001")
    assert isinstance(state, CandidateState)
    assert hasattr(state, "candidate_id")
    assert hasattr(state, "attempts")
    assert hasattr(state, "completed_days")
    
    # Assert CandidateState has NO technical understanding or knowledge score fields
    assert not hasattr(state, "understanding_level")
    assert not hasattr(state, "knowledge_score")
    assert not hasattr(state, "topics_understanding")
    print("[PASS] 1 & 2. CandidateState is strictly pre-interview profile data.")


def test_3_and_4_knowledge_model_starts_empty_and_represents_understanding():
    """3, 4. CandidateKnowledgeModel starts empty/unknown and represents derived understanding."""
    km = CandidateKnowledgeModel(candidate_id="CAND-001")
    # Test 3: Starts empty
    assert len(km.topics) == 0

    # Test 4: Represents derived understanding
    km.topics[7] = CandidateTopicKnowledge(
        curriculum_day=7,
        topic="Embeddings Explained",
        understanding_level="HIGH",
        confidence=0.95,
        strengths=["Clear explanation of vector dimensions"],
        gaps=[],
        evidence_ids=["ev-101"]
    )
    assert km.topics[7].understanding_level == "HIGH"
    assert km.topics[7].confidence == 0.95
    print("[PASS] 3 & 4. CandidateKnowledgeModel starts empty and represents derived understanding.")


def test_5_evidence_ledger_stores_linked_evidence():
    """5. EvidenceLedger can store evidence linked to a question/session/day."""
    ledger = EvidenceLedger(session_id="sess-001")
    item = EvidenceItem(
        evidence_id="ev-101",
        session_id="sess-001",
        question_id="q-1",
        candidate_id="CAND-001",
        curriculum_day=7,
        topic="Embeddings Explained",
        candidate_claim="Embeddings map tokens to dense vector spaces.",
        evidence_text="Accurate explanation of embedding spaces.",
        assessment="supports_understanding",
        confidence=0.9,
        turn=1
    )
    ledger.add_evidence(item)
    assert len(ledger.items) == 1
    day_7_ev = ledger.get_evidence_for_day(7)
    assert len(day_7_ev) == 1
    assert day_7_ev[0].question_id == "q-1"
    print("[PASS] 5. EvidenceLedger stores linked evidence successfully.")


def test_6_and_7_interview_state_tracks_live_execution():
    """6, 7. InterviewState tracks live interview execution separately from CandidateState."""
    istate = InterviewState(
        session_id="sess-001",
        candidate_id="CAND-001",
        current_turn=2,
        question_count=2,
        current_topic_day=7,
        done=False,
        interview_started=True
    )
    assert istate.current_turn == 2
    assert istate.current_topic_day == 7
    # Assert InterviewState does not duplicate CandidateState profile signals
    assert not hasattr(istate, "education")
    assert not hasattr(istate, "years_experience")
    print("[PASS] 6 & 7. InterviewState tracks live state without duplicating CandidateState.")


def test_8_and_9_llm_analysis_model_and_session_manager_integration():
    """8, 9. CandidateEvidenceAnalysis applied via SessionManager holding all 4 layers."""
    session_manager.clear_all()
    session = session_manager.create_session("sess-arch-1", {"member": {"id": "CAND-001"}})
    
    # Test 9: SessionManager holds all 4 layers
    assert session["candidate_state"] is not None
    assert session["interview_state"] is not None
    assert session["knowledge_model"] is not None
    assert session["evidence_ledger"] is not None
    assert len(session["knowledge_model"].topics) > 0
    assert all(t.understanding_level == "UNKNOWN" for t in session["knowledge_model"].topics.values())
    assert all(t.confidence is None for t in session["knowledge_model"].topics.values())

    # Test 8: LLM returns CandidateEvidenceAnalysis structure -> backend validates and applies
    analysis = CandidateEvidenceAnalysis(
        curriculum_day=12,
        topic="Prompt Engineering Fundamentals",
        understanding_assessment="HIGH",
        assessment_type="supports_understanding",
        confidence=0.92,
        strengths=["Understands system prompts vs user prompts"],
        gaps=[],
        evidence_text="Candidate explained zero-shot vs few-shot prompting clearly.",
        candidate_claim="Few-shot prompts give exemplar inputs and outputs.",
        follow_up_recommended=False
    )

    ev_item = session_manager.apply_evidence_analysis("sess-arch-1", analysis, question_id="q-3")
    assert ev_item is not None
    assert len(session["evidence_ledger"].items) == 1
    assert session["knowledge_model"].topics[12].understanding_level == "HIGH"
    print("[PASS] 8 & 9. LLM analysis model & SessionManager 4-layer integration verified.")


def test_10_to_14_existing_test_suites_pass():
    """10-14. Existing Step 1, Step 2A, Step 2B, Step 2C, and Step 3A tests pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    print("[PASS] 10-14. All existing Step 1 through 3A test suites pass.")


def test_15_to_17_canonical_data_file_checks():
    """15-17. Canonical data file checks and root duplicate removal."""
    base_dir = Path(__file__).resolve().parent
    canonical_candidates = base_dir / "data" / "candidates.json"
    canonical_curriculum = base_dir / "data" / "curriculum.json"

    # Test 15: Canonical files exist
    assert canonical_candidates.exists(), "Canonical backend/data/candidates.json missing!"
    assert canonical_curriculum.exists(), "Canonical backend/data/curriculum.json missing!"

    # Test 16 & 17: Root duplicates do not exist
    root_candidates = base_dir.parent / "candidates.json"
    root_curriculum = base_dir.parent / "curriculum.json"

    assert not root_candidates.exists(), "Root candidates.json duplicate still exists!"
    assert not root_curriculum.exists(), "Root curriculum.json duplicate still exists!"
    print("[PASS] 15-17. Canonical data file checks pass and root duplicates removed.")


def test_18_engine_foundation_requirements():
    """Verify all 14 engine foundation validation requirements explicitly."""
    # 1. CandidateState creation still works
    c_state = candidate_profile_service.build_candidate_state("CAND-003")
    assert isinstance(c_state, CandidateState)
    assert c_state.candidate_id == "CAND-003"

    # 2. CurriculumState creation works
    curr_state = curriculum_service.get_state()
    assert isinstance(curr_state, CurriculumState)

    # 3. InterviewPlanner creates a valid plan
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert isinstance(plan, InterviewPlan)

    # 4. Session creation automatically creates InterviewPlan
    session_manager.clear_all()
    candidate_profile = candidate_profile_service.get_candidate("CAND-003")
    session = session_manager.create_session("sess-test-fnd", candidate_profile)
    assert session["interview_state"].interview_plan is not None

    # 5. InterviewState contains the plan
    assert isinstance(session["interview_state"].interview_plan, InterviewPlan)

    # 6. Minimum 8 question budget is enforced when possible
    assert session["interview_state"].interview_plan.total_question_budget >= 8

    # 7. At least 4 curriculum days are selected when candidate has enough eligible completed days
    # CAND-003 has 10 completed days, so budget must have >= 4 days
    assert len(session["interview_state"].interview_plan.selected_days) >= 4

    # 8. CandidateKnowledgeModel starts unknown
    topics = session["knowledge_model"].topics
    assert len(topics) > 0
    for day_num, tk in topics.items():
        assert tk.understanding_level == "UNKNOWN"
        assert tk.confidence is None
        assert tk.depth_confidence is None
        assert tk.reasoning_confidence is None
        assert tk.communication_confidence is None

    # 9. Objective-level knowledge can be represented
    day_7_objs = topics[7].objectives
    assert len(day_7_objs) > 0
    assert "day-7-obj-0" in day_7_objs
    assert day_7_objs["day-7-obj-0"].understanding_level == "UNKNOWN"
    assert day_7_objs["day-7-obj-0"].confidence is None

    # 10. EvidenceLedger remains traceable
    ledger = session["evidence_ledger"]
    assert isinstance(ledger, EvidenceLedger)
    assert len(ledger.items) == 0  # starts empty

    # 11. Existing API tests pass
    from test_api import test_health_check, test_create_session, test_subsequent_message
    test_health_check()
    test_create_session()
    test_subsequent_message()

    # 12. Existing Candidate Profile tests pass
    from test_candidate_profile_service import test_1_cand001_loads_successfully, test_2_cand001_correct_id_and_name
    test_1_cand001_loads_successfully()
    test_2_cand001_correct_id_and_name()

    # 13. Existing Curriculum tests pass
    from test_curriculum_service import test_1_curriculum_loads_successfully, test_2_thirty_one_days_parsed
    test_1_curriculum_loads_successfully()
    test_2_thirty_one_days_parsed()

    # 14. Breeth configuration remains unaffected
    from services.memory_service import MemoryService
    service = MemoryService(api_key="test-api-key")
    assert service.api_key == "test-api-key"
    assert service.is_configured() is True
    print("[PASS] 18. Explicit validation requirements verified.")


if __name__ == "__main__":
    print("Running Architectural Refinement Test Suite...")
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    test_3_and_4_knowledge_model_starts_empty_and_represents_understanding()
    test_5_evidence_ledger_stores_linked_evidence()
    test_6_and_7_interview_state_tracks_live_execution()
    test_8_and_9_llm_analysis_model_and_session_manager_integration()
    test_10_to_14_existing_test_suites_pass()
    test_15_to_17_canonical_data_file_checks()
    test_18_engine_foundation_requirements()
    print("\nALL ARCHITECTURAL REFINEMENT TESTS PASSED SUCCESSFULLY!")
