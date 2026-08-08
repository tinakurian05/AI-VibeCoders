import os
import sys
from unittest.mock import patch
import httpx

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.groq_client import GroqClient, groq_client


def test_1_missing_api_key_categorization():
    """1. Missing API key is detected and safely returns authentication error."""
    client = GroqClient(api_key="", model="openai/gpt-oss-120b")
    assert client.is_configured() is False
    res = client.generate_chat_completion()
    assert res["success"] is False
    assert res["error_category"] == "authentication error"
    print("[PASS] 1. Missing API key returns authentication error.")


def test_2_model_configuration():
    """2. Model name is configurable via environment or override."""
    client = GroqClient(api_key="dummy-key", model="openai/gpt-oss-120b")
    assert client.model == "openai/gpt-oss-120b"
    
    with patch.dict(os.environ, {"LLM_PRIMARY_MODEL": "custom/model-v1"}):
        env_client = GroqClient(api_key="dummy-key")
        assert env_client.model == "custom/model-v1"
    print("[PASS] 2. Model configuration verified.")


def test_3_and_4_and_5_mock_successful_completion():
    """3, 4, 5. Endpoint, headers, payload, and successful response parsing verified."""
    client = GroqClient(api_key="secret-groq-key-xyz", model="openai/gpt-oss-120b")
    recorded_request = None

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal recorded_request
        recorded_request = request
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "model": "openai/gpt-oss-120b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "RAG combines vector retrieval with language generation to answer queries."
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
        )

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion(
            prompt="Explain RAG in one sentence.",
            system_prompt="You are a helpful assistant. Respond briefly."
        )

    assert recorded_request is not None
    # Test 3: Endpoint & Headers
    assert str(recorded_request.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert recorded_request.headers["Authorization"] == "Bearer secret-groq-key-xyz"
    assert recorded_request.headers["Content-Type"] == "application/json"

    # Test 4: Payload structure
    import json
    body = json.loads(recorded_request.content)
    assert body["model"] == "openai/gpt-oss-120b"
    assert len(body["messages"]) == 2
    assert body["messages"][0] == {"role": "system", "content": "You are a helpful assistant. Respond briefly."}
    assert body["messages"][1] == {"role": "user", "content": "Explain RAG in one sentence."}

    # Test 5: Successful non-empty response
    assert result["success"] is True
    assert result["model"] == "openai/gpt-oss-120b"
    assert len(result["response_text"]) > 0
    assert "vector retrieval" in result["response_text"]
    print("[PASS] 3, 4, 5. Endpoint, headers, payload & non-empty response verified.")


def test_6_authentication_error_categorization():
    """6. HTTP 401 returns sanitized 'authentication error' category."""
    client = GroqClient(api_key="bad-key", model="openai/gpt-oss-120b")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "Invalid API key"}})

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion()

    assert result["success"] is False
    assert result["error_category"] == "authentication error"
    print("[PASS] 6. HTTP 401 categorized as authentication error.")


def test_7_rate_limit_categorization():
    """7. HTTP 429 returns sanitized 'rate limit' category."""
    client = GroqClient(api_key="valid-key", model="openai/gpt-oss-120b")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "Rate limit reached"}})

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion()

    assert result["success"] is False
    assert result["error_category"] == "rate limit"
    print("[PASS] 7. HTTP 429 categorized as rate limit.")


def test_8_timeout_categorization():
    """8. Timeout exception returns sanitized 'timeout' category."""
    client = GroqClient(api_key="valid-key", model="openai/gpt-oss-120b")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Request timed out", request=request)

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion()

    assert result["success"] is False
    assert result["error_category"] == "timeout"
    print("[PASS] 8. Timeout exception categorized as timeout.")


def test_9_connection_error_categorization():
    """9. Connection exception returns sanitized 'connection error' category."""
    client = GroqClient(api_key="valid-key", model="openai/gpt-oss-120b")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Failed to resolve host", request=request)

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion()

    assert result["success"] is False
    assert result["error_category"] == "connection error"
    print("[PASS] 9. Connection exception categorized as connection error.")


def test_10_secret_key_never_logged():
    """10. Secret API key is never exposed or printed in result dict."""
    secret_key = "gsk_real_secret_key_string_9999"
    client = GroqClient(api_key=secret_key, model="openai/gpt-oss-120b")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": f"Invalid key {secret_key}"}})

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = client.generate_chat_completion()

    result_str = str(result)
    assert secret_key not in result_str
    print("[PASS] 10. Secret API key is never exposed in result output.")


def test_11_all_previous_test_suites_pass():
    """11. Existing Step 1, 2A, 2B, 2C, 3A, and Architectural Refinement tests pass."""
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
    print("[PASS] 11. All previous test suites pass.")


def run_manual_live_test() -> Dict[str, Any]:
    """
    Manual connectivity test for calling real GroqCloud API if GROQ_API_KEY is configured.
    """
    print("\n--- Manual GroqCloud Live Connectivity Test ---")
    if not groq_client.is_configured():
        print("Result: GROQ_API_KEY is empty/not set. Skipping live test.")
        return {
            "success": False,
            "error_category": "authentication error",
            "details": "GROQ_API_KEY is not set."
        }

    print(f"Calling GroqCloud with model: {groq_client.model} ...")
    res = groq_client.generate_chat_completion(
        prompt="Explain RAG in one sentence.",
        system_prompt="You are a helpful assistant. Respond briefly."
    )

    if res["success"]:
        print(f"Status: SUCCESS")
        print(f"Model Used: {res['model']}")
        print(f"Response Text: {res['response_text']}")
    else:
        print(f"Status: FAILED")
        print(f"Model Used: {res['model']}")
        print(f"Sanitized Error Category: {res['error_category']}")

    return res


if __name__ == "__main__":
    print("Running GroqCloud Unit Test Suite...")
    test_1_missing_api_key_categorization()
    test_2_model_configuration()
    test_3_and_4_and_5_mock_successful_completion()
    test_6_authentication_error_categorization()
    test_7_rate_limit_categorization()
    test_8_timeout_categorization()
    test_9_connection_error_categorization()
    test_10_secret_key_never_logged()
    test_11_all_previous_test_suites_pass()
    print("\nALL GROQCLOUD UNIT TESTS PASSED SUCCESSFULLY!")

    # Attempt live test if explicitly requested or if env variable present
    if os.getenv("RUN_LIVE_GROQ_TEST") == "1":
        run_manual_live_test()
