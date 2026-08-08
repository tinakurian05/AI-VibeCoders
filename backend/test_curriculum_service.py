import hashlib
import os
import sys
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.curriculum_service import curriculum_service, CurriculumService
from models.interview import CurriculumDay, CurriculumModule, CurriculumState


def test_1_curriculum_loads_successfully():
    """1. Curriculum loads successfully."""
    state = curriculum_service.load_curriculum()
    assert isinstance(state, CurriculumState)
    assert state.cohort.startswith("AI Cohort")
    print("[PASS] 1. Curriculum loads successfully.")


def test_2_thirty_one_days_parsed():
    """2. The 31-day curriculum is parsed."""
    state = curriculum_service.get_state()
    assert len(state.days) == 31, f"Expected 31 days, got {len(state.days)}"
    for day_num in range(1, 32):
        assert day_num in state.days, f"Day {day_num} missing from state.days"
    print("[PASS] 2. All 31 curriculum days are parsed.")


def test_3_day_lookup_works():
    """3. Day lookup works."""
    day1 = curriculum_service.get_day(1)
    assert isinstance(day1, CurriculumDay)
    assert day1.day == 1
    assert day1.title == "VS Code & Python Environment Setup"
    assert day1.type == "SETUP"
    print("[PASS] 3. Day lookup works.")


def test_4_invalid_day_lookup_raises_error():
    """4. Invalid day lookup raises a clear error."""
    raised = False
    try:
        curriculum_service.get_day(99)
    except ValueError as e:
        raised = True
        assert "99" in str(e)
    assert raised, "Expected ValueError for day 99 was not raised."
    print("[PASS] 4. Invalid day lookup raises ValueError.")


def test_5_multiple_day_lookup_works():
    """5. Multiple day lookup works."""
    days = curriculum_service.get_days([1, 7, 12])
    assert len(days) == 3
    assert days[0].day == 1
    assert days[1].day == 7
    assert days[2].day == 12
    assert days[1].title == "Embeddings Explained"
    print("[PASS] 5. Multiple day lookup works.")


def test_6_module_information_preserved():
    """6. Module information is preserved."""
    module1 = curriculum_service.get_module(1)
    assert isinstance(module1, CurriculumModule)
    assert module1.module_id == 1
    assert module1.title == "Environment & Tooling"
    assert module1.day_range == [1, 3]
    # Days 1, 2, 3 should be in module1.days
    assoc_day_nums = [d.day for d in module1.days]
    assert assoc_day_nums == [1, 2, 3]
    print("[PASS] 6. Module information is preserved.")


def test_7_tools_are_preserved():
    """7. Tools are preserved."""
    day1 = curriculum_service.get_day(1)
    expected_tools = ["VS Code", "Python", "Python Extension", "Pylance", "Virtual Environment"]
    assert day1.tools == expected_tools
    print("[PASS] 7. Tools are preserved.")


def test_8_learning_objectives_preserved():
    """8. Learning objectives are preserved."""
    day1 = curriculum_service.get_day(1)
    assert len(day1.objectives) == 5
    assert "Install VS Code and Python on your machine" in day1.objectives
    print("[PASS] 8. Learning objectives are preserved.")


def test_9_parsed_curriculum_does_not_modify_file():
    """9. The parsed curriculum does not modify curriculum.json."""
    file_path = Path(__file__).resolve().parent / "data" / "curriculum.json"
    with open(file_path, "rb") as f:
        hash_before = hashlib.sha256(f.read()).hexdigest()

    # Perform multiple service calls
    cs = CurriculumService(file_path)
    cs.load_curriculum()
    cs.get_day(1)
    cs.get_module(1)

    with open(file_path, "rb") as f:
        hash_after = hashlib.sha256(f.read()).hexdigest()

    assert hash_before == hash_after, "curriculum.json was modified!"
    print("[PASS] 9. Parsed curriculum does not modify curriculum.json.")


def test_10_existing_tests_pass():
    """10. Existing Step 1 and Step 2A tests still pass."""
    # Import and run Step 1 & 2A test modules
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully, test_9_failed_mission_not_in_completed_days

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_9_failed_mission_not_in_completed_days()
    print("[PASS] 10. Existing Step 1 and Step 2A tests pass.")


if __name__ == "__main__":
    print("Running STEP 2B Test Suite...")
    test_1_curriculum_loads_successfully()
    test_2_thirty_one_days_parsed()
    test_3_day_lookup_works()
    test_4_invalid_day_lookup_raises_error()
    test_5_multiple_day_lookup_works()
    test_6_module_information_preserved()
    test_7_tools_are_preserved()
    test_8_learning_objectives_preserved()
    test_9_parsed_curriculum_does_not_modify_file()
    test_10_existing_tests_pass()
    print("\nALL STEP 2B TESTS PASSED SUCCESSFULLY!")
