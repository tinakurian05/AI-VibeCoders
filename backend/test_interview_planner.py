import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.candidate_profile_service import candidate_profile_service
from services.curriculum_service import curriculum_service
from services.interview_planner import interview_planner, InterviewPlanner
from models.interview import CandidateState, CurriculumState, InterviewPlan


def get_states(candidate_id: str):
    c_state = candidate_profile_service.build_candidate_state(candidate_id)
    curr_state = curriculum_service.get_state()
    return c_state, curr_state


def test_1_planner_loads_states_successfully():
    """1. Planner loads CandidateState + CurriculumState successfully."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert isinstance(plan, InterviewPlan)
    assert plan.candidate_id == "CAND-001"
    print("[PASS] 1. Planner loads CandidateState + CurriculumState successfully.")


def test_2_candidate_with_four_plus_days():
    """2. A candidate with >=4 completed days receives >=4 selected curriculum days."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert len(plan.selected_days) >= 4
    assert plan.min_days_met is True
    print("[PASS] 2. Candidate with >=4 completed days receives >=4 selected curriculum days.")


def test_3_total_question_budget_at_least_eight():
    """3. Total question budget is >= 8."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert plan.total_question_budget >= 8
    assert plan.min_questions_met is True
    print("[PASS] 3. Total question budget is >= 8.")


def test_4_selected_days_are_all_completed_days():
    """4. Selected days are all completed days."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    for day in plan.selected_days:
        assert day in c_state.completed_days
    print("[PASS] 4. Selected days are all completed days.")


def test_5_skipped_days_never_selected():
    """5. Skipped days are never selected."""
    c_state, curr_state = get_states("CAND-001")
    assert 29 in c_state.skipped_days
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert 29 not in plan.selected_days
    print("[PASS] 5. Skipped days are never selected.")


def test_6_failed_missions_never_selected():
    """6. Failed missions are never selected."""
    # CAND-010 has days 8 and 10 with passed: false
    c_state, curr_state = get_states("CAND-010")
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert 8 not in plan.selected_days
    assert 10 not in plan.selected_days
    print("[PASS] 6. Failed missions are never selected.")


def test_7_module_diversity_preferred():
    """7. Module diversity is preferred when enough eligible modules exist."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    module_ids = [t.module_id for t in plan.topic_plans]
    # At least 4 distinct module IDs should be present
    unique_modules = set(module_ids)
    assert len(unique_modules) >= 4
    print("[PASS] 7. Module diversity is preferred.")


def test_8_higher_attempt_topics_receive_higher_priority():
    """8. Higher-attempt topics receive appropriate higher probing priority."""
    c_state, curr_state = get_states("CAND-001")
    # Day 12 has 4 attempts, Day 7 has 1 attempt
    plan = interview_planner.plan_interview(c_state, curr_state)
    day_12_topic = next((t for t in plan.topic_plans if t.day == 12), None)
    day_7_topic = next((t for t in plan.topic_plans if t.day == 7), None)
    if day_12_topic and day_7_topic:
        assert day_12_topic.priority_score > day_7_topic.priority_score
        assert "4 attempt" in day_12_topic.probing_reason
    print("[PASS] 8. Higher-attempt topics receive higher priority.")


def test_9_attempts_do_not_label_candidate_weak():
    """9. Attempts do not automatically label a candidate as weak."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    for topic in plan.topic_plans:
        assert "weak" not in topic.probing_reason.lower()
        assert "failure" not in topic.probing_reason.lower()
    print("[PASS] 9. Attempts do not label a candidate as weak.")


def test_10_follow_up_allowed_represented():
    """10. follow_up_allowed is represented in the plan."""
    c_state, curr_state = get_states("CAND-001")
    plan = interview_planner.plan_interview(c_state, curr_state)
    for topic in plan.topic_plans:
        assert topic.follow_up_allowed is True
    print("[PASS] 10. follow_up_allowed is represented in the plan.")


def test_11_deterministic_result():
    """11. Same input state produces the exact same InterviewPlan."""
    c_state, curr_state = get_states("CAND-001")
    plan1 = interview_planner.plan_interview(c_state, curr_state)
    plan2 = interview_planner.plan_interview(c_state, curr_state)
    assert plan1.model_dump() == plan2.model_dump()
    print("[PASS] 11. Same input state produces identical InterviewPlan every time.")


def test_12_candidate_fewer_than_four_completed_days():
    """12. Candidate with fewer than 4 eligible completed days is handled gracefully."""
    # Create synthetic CandidateState with only 2 completed days
    c_state = CandidateState(
        candidate_id="CAND-FEW",
        name="Test Few",
        job_role="Engineer",
        years_experience=2,
        education="BS",
        status="IN_PROGRESS",
        completed_days=[1, 3],
        skipped_days=[],
        attempts={1: 1, 3: 2},
        mission_titles={1: "Setup", 3: "React"},
        signals={"commitDays": 2, "missionsCompleted": 2, "missionsFirstTry": 1}
    )
    curr_state = curriculum_service.get_state()
    plan = interview_planner.plan_interview(c_state, curr_state)
    assert len(plan.selected_days) == 2
    assert plan.min_days_met is False
    assert plan.total_question_budget >= 8  # Still allocates 8 total question slots across 2 days (4 each)
    assert plan.notes is not None
    assert "Minimum 4-day requirement cannot be fully satisfied" in plan.notes
    print("[PASS] 12. Candidate with fewer than 4 completed days is handled gracefully.")


def test_13_existing_tests_pass():
    """13. Existing Step 1, Step 2A, and Step 2B tests still pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    print("[PASS] 13. Existing Step 1, Step 2A, and Step 2B tests pass.")


if __name__ == "__main__":
    print("Running STEP 2C Test Suite...")
    test_1_planner_loads_states_successfully()
    test_2_candidate_with_four_plus_days()
    test_3_total_question_budget_at_least_eight()
    test_4_selected_days_are_all_completed_days()
    test_5_skipped_days_never_selected()
    test_6_failed_missions_never_selected()
    test_7_module_diversity_preferred()
    test_8_higher_attempt_topics_receive_higher_priority()
    test_9_attempts_do_not_label_candidate_weak()
    test_10_follow_up_allowed_represented()
    test_11_deterministic_result()
    test_12_candidate_fewer_than_four_completed_days()
    test_13_existing_tests_pass()
    print("\nALL STEP 2C TESTS PASSED SUCCESSFULLY!")
