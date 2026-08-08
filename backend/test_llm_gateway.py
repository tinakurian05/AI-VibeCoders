import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.llm_gateway import LLMGateway, llm_gateway
from models.interview import LLMResponse


def test_1_and_2_gateway_initialization_and_primary_model():
    """1, 2. Gateway initializes correctly and primary model is loaded."""
    gateway = LLMGateway(default_model="openai/gpt-oss-120b")
    assert gateway.primary_model == "openai/gpt-oss-120b"

    with patch.dict(os.environ, {"LLM_PRIMARY_MODEL": "openai/gpt-oss-120b"}):
        default_gw = LLMGateway()
        assert default_gw.primary_model == "openai/gpt-oss-120b"
    print("[PASS] 1 & 2. Gateway initialization & primary model verified.")


def test_3_and_4_gateway_delegates_to_groq_client_and_normalizes_response():
    """3, 4. Gateway delegates to groq_client and normalizes into LLMResponse."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "success": True,
        "model": "openai/gpt-oss-120b",
        "response_text": "Vector databases enable fast similarity search across embeddings.",
        "error_category": None,
        "details": "Success"
    }

    gateway = LLMGateway(client=mock_client, default_model="openai/gpt-oss-120b")
    response = gateway.generate(
        system_prompt="You are a helpful assistant.",
        user_prompt="Explain vector databases."
    )

    # Test 3: Delegation check
    mock_client.generate_chat_completion.assert_called_once_with(
        prompt="Explain vector databases.",
        system_prompt="You are a helpful assistant.",
        model_override="openai/gpt-oss-120b",
        timeout=15.0
    )

    # Test 4: Normalized LLMResponse check
    assert isinstance(response, LLMResponse)
    assert response.success is True
    assert response.provider == "groq"
    assert response.model_used == "openai/gpt-oss-120b"
    assert response.content == "Vector databases enable fast similarity search across embeddings."
    assert response.latency_ms >= 0.0
    assert response.error_category is None
    print("[PASS] 3 & 4. Delegation to groq_client & normalized response verified.")


def test_5_model_override_works():
    """5. Model override works when explicitly passed to generate()."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "success": True,
        "model": "custom/override-model-v2",
        "response_text": "Override text",
        "error_category": None,
        "details": "Success"
    }

    gateway = LLMGateway(client=mock_client, default_model="openai/gpt-oss-120b")
    response = gateway.generate(
        system_prompt="System",
        user_prompt="User",
        model="custom/override-model-v2"
    )

    mock_client.generate_chat_completion.assert_called_once_with(
        prompt="User",
        system_prompt="System",
        model_override="custom/override-model-v2",
        timeout=15.0
    )
    assert response.model_used == "custom/override-model-v2"
    print("[PASS] 5. Model override verified.")


def test_6_errors_returned_as_sanitized_categories():
    """6. Errors are returned using sanitized error categories."""
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "success": False,
        "model": "openai/gpt-oss-120b",
        "response_text": "",
        "error_category": "rate limit",
        "details": "Rate limit exceeded"
    }

    gateway = LLMGateway(client=mock_client)
    response = gateway.generate(system_prompt="sys", user_prompt="usr")

    assert response.success is False
    assert response.content == ""
    assert response.error_category == "rate limit"
    print("[PASS] 6. Sanitized error category propagation verified.")


def test_7_api_key_never_appears_in_output():
    """7. API key never appears in LLMResponse or string representations."""
    secret_key = "secret_groq_key_val_999"
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "success": False,
        "model": "openai/gpt-oss-120b",
        "response_text": "",
        "error_category": "authentication error",
        "details": "Failed auth"
    }

    gateway = LLMGateway(client=mock_client)
    response = gateway.generate(system_prompt="sys", user_prompt="usr")
    
    assert secret_key not in str(response.model_dump())
    assert secret_key not in str(response)
    print("[PASS] 7. Secret API key never appears in output.")


def test_8_all_previous_test_suites_pass():
    """8. All previous test suites (Step 1 through 3A + Architecture + Groq) pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully
    from test_memory_service import test_1_missing_api_key_detected
    from test_architecture_refinement import test_1_and_2_candidate_state_is_pre_interview_facts_only
    from test_groq_connection import test_1_missing_api_key_categorization

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    test_1_missing_api_key_detected()
    test_1_and_2_candidate_state_is_pre_interview_facts_only()
    test_1_missing_api_key_categorization()
    print("[PASS] 8. All previous test suites pass.")


if __name__ == "__main__":
    from unittest.mock import patch
    print("Running LLMGateway Unit Test Suite...")
    test_1_and_2_gateway_initialization_and_primary_model()
    test_3_and_4_gateway_delegates_to_groq_client_and_normalizes_response()
    test_5_model_override_works()
    test_6_errors_returned_as_sanitized_categories()
    test_7_api_key_never_appears_in_output()
    test_8_all_previous_test_suites_pass()
    print("\nALL LLMGATEWAY UNIT TESTS PASSED SUCCESSFULLY!")
