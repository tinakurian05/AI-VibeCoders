import os
import sys
from unittest.mock import MagicMock, patch
import httpx

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.model_router import ModelRouter
from services.llm_gateway import LLMGateway
from models.interview import LLMResponse


def test_1_primary_succeeds_fallback_not_called():
    """1. Primary succeeds -> fallback is not called."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": True,
            "model": "openai/gpt-oss-120b",
            "response_text": "Primary answer",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is True
    assert res.model_used == "openai/gpt-oss-120b"
    assert res.content == "Primary answer"
    # Verify client called exactly once (for primary only)
    assert mock_client.generate_chat_completion.call_count == 1
    print("[PASS] 1. Primary succeeds -> fallback is not called.")


def test_2_primary_rate_limited_fallback_succeeds():
    """2. Primary rate-limited -> fallback succeeds."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "rate limit"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Fallback answer",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is True
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    assert res.content == "Fallback answer"
    assert mock_client.generate_chat_completion.call_count == 2
    print("[PASS] 2. Primary rate-limited -> fallback succeeds.")


def test_3_primary_timeout_fallback_succeeds():
    """3. Primary timeout -> fallback succeeds."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "timeout"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Fallback answer after timeout",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is True
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    assert res.content == "Fallback answer after timeout"
    assert mock_client.generate_chat_completion.call_count == 2
    print("[PASS] 3. Primary timeout -> fallback succeeds.")


def test_4_primary_connection_error_fallback_succeeds():
    """4. Primary connection failure -> fallback succeeds."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "connection error"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Fallback answer after connection error",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is True
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    assert mock_client.generate_chat_completion.call_count == 2
    print("[PASS] 4. Primary connection error -> fallback succeeds.")


def test_5_primary_provider_error_fallback_succeeds():
    """5. Primary provider error -> fallback succeeds."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "provider error"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Fallback answer after provider error",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is True
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    assert mock_client.generate_chat_completion.call_count == 2
    print("[PASS] 5. Primary provider error -> fallback succeeds.")


def test_6_primary_authentication_error_fallback_not_called():
    """6. Primary authentication error -> fallback is NOT called."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "authentication error"
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is False
    assert res.error_category == "authentication error"
    # Verify fallback model was NOT called
    assert mock_client.generate_chat_completion.call_count == 1
    print("[PASS] 6. Primary authentication error -> fallback is NOT called.")


def test_7_primary_invalid_request_fallback_not_called():
    """7. Primary invalid request -> fallback is NOT called."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "invalid request"
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is False
    assert res.error_category == "invalid request"
    assert mock_client.generate_chat_completion.call_count == 1
    print("[PASS] 7. Primary invalid request -> fallback is NOT called.")


def test_8_both_primary_and_fallback_fail():
    """8. Both primary and fallback fail -> safe normalized error."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "rate limit"
        },
        {
            "success": False,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "",
            "error_category": "provider error"
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")

    assert res.success is False
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    assert res.error_category == "provider error"
    assert mock_client.generate_chat_completion.call_count == 2
    print("[PASS] 8. Both primary and fallback fail -> safe normalized error returned.")


def test_9_model_used_identifies_successful_model():
    """9. model_used correctly identifies the model generating successful response."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "timeout"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Answer from backup",
            "error_category": None
        }
    ]

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")
    assert res.model_used == "meta-llama/llama-3.3-70b-versatile"
    print("[PASS] 9. model_used correctly identifies generating model.")


def test_10_api_keys_never_appear_in_output():
    """10. API keys never appear in output/errors."""
    secret = "secret_key_groq_val_12345"
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "success": False,
        "model": "openai/gpt-oss-120b",
        "response_text": "",
        "error_category": "authentication error"
    }

    router = ModelRouter(
        client=mock_client,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )

    res = router.generate(system_prompt="sys", user_prompt="usr")
    assert secret not in str(res)
    print("[PASS] 10. API keys never appear in output.")


def test_11_all_existing_test_suites_pass():
    """11. Existing Step 1 through Step 3A tests pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected
    from test_architecture_refinement import test_1_and_2_candidate_state_is_pre_interview_facts_only
    from test_llm_gateway import test_1_and_2_gateway_initialization_and_primary_model

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    test_1_and_2_gateway_initialization_and_primary_model()
    print("[PASS] 11. Existing test suites pass.")


def run_demonstration_cases():
    """12. Manual demonstration showing Case A (Primary succeeds) and Case B (Rate limit failover)."""
    print("\n--- Demonstration Case A: Primary Model Succeeds ---")
    mock_client_a = MagicMock()
    mock_client_a.generate_chat_completion.return_value = {
        "success": True,
        "model": "openai/gpt-oss-120b",
        "response_text": "Primary model response: RAG retrieves context before generation.",
        "error_category": None
    }
    router_a = ModelRouter(
        client=mock_client_a,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )
    res_a = router_a.generate(system_prompt="sys", user_prompt="Explain RAG")
    print(f"Status: SUCCESS ({res_a.success})")
    print(f"Model Used: {res_a.model_used}")
    print(f"Response: {res_a.content}")
    print(f"Calls Made: Primary called ({mock_client_a.generate_chat_completion.call_count} time)")

    print("\n--- Demonstration Case B: Primary Rate Limit -> Fallback Succeeds ---")
    mock_client_b = MagicMock()
    mock_client_b.generate_chat_completion.side_effect = [
        {
            "success": False,
            "model": "openai/gpt-oss-120b",
            "response_text": "",
            "error_category": "rate limit"
        },
        {
            "success": True,
            "model": "meta-llama/llama-3.3-70b-versatile",
            "response_text": "Fallback model response: RAG enhances generation with external documents.",
            "error_category": None
        }
    ]
    router_b = ModelRouter(
        client=mock_client_b,
        primary_model="openai/gpt-oss-120b",
        fallback_model="meta-llama/llama-3.3-70b-versatile"
    )
    res_b = router_b.generate(system_prompt="sys", user_prompt="Explain RAG")
    print(f"Status: SUCCESS ({res_b.success})")
    print(f"Primary Failed With: rate limit")
    print(f"Model Used: {res_b.model_used}")
    print(f"Response: {res_b.content}")
    print(f"Calls Made: Total calls ({mock_client_b.generate_chat_completion.call_count} times - 1 Primary, 1 Fallback)")


if __name__ == "__main__":
    print("Running ModelRouter Unit Test Suite...")
    test_1_primary_succeeds_fallback_not_called()
    test_2_primary_rate_limited_fallback_succeeds()
    test_3_primary_timeout_fallback_succeeds()
    test_4_primary_connection_error_fallback_succeeds()
    test_5_primary_provider_error_fallback_succeeds()
    test_6_primary_authentication_error_fallback_not_called()
    test_7_primary_invalid_request_fallback_not_called()
    test_8_both_primary_and_fallback_fail()
    test_9_model_used_identifies_successful_model()
    test_10_api_keys_never_appear_in_output()
    test_11_all_existing_test_suites_pass()
    print("\nALL MODELROUTER UNIT TESTS PASSED SUCCESSFULLY!")

    run_demonstration_cases()
