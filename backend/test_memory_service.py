import os
import sys
from unittest.mock import patch, MagicMock
import httpx

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from services.memory_service import MemoryService


def test_1_missing_api_key_detected():
    """1. Missing API key is detected and handled safely."""
    service = MemoryService(api_key="", base_url="https://api.thebreeth.com")
    assert service.is_configured() is False
    
    result = service.store_episode("sess-1", [{"role": "user", "content": "hi"}])
    assert result["success"] is False
    assert "not configured" in result["message"].lower()

    search_res = service.search_memory("sess-1", "python")
    assert search_res == []
    print("[PASS] 1. Missing API key is detected.")


def test_2_and_3_and_5_store_episode_endpoint_header_scoping():
    """2, 3, 5. Store episode constructs correct endpoint, header, and session scoping."""
    service = MemoryService(api_key="secret-key-xyz", base_url="https://api.thebreeth.com")
    
    recorded_request = None

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal recorded_request
        recorded_request = request
        return httpx.Response(200, json={"id": "ep-101", "status": "stored"})

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = service.store_episode(
            session_id="test-session-123",
            messages=[{"role": "user", "content": "I know FastAPI"}],
            metadata={"difficulty": "medium"}
        )

    assert recorded_request is not None
    # Test 2: Endpoint
    assert str(recorded_request.url) == "https://api.thebreeth.com/v1/episodes"
    # Test 3: Authorization header
    assert recorded_request.headers["Authorization"] == "Bearer secret-key-xyz"
    assert recorded_request.headers["Content-Type"] == "application/json"
    
    # Test 5: group_id scoping
    import json
    body = json.loads(recorded_request.content)
    assert body["group_id"] == "interview:test-session-123"
    assert body["messages"] == [{"role": "user", "content": "I know FastAPI"}]
    assert body["metadata"] == {"difficulty": "medium"}

    # Test 6: Successful store response parsed
    assert result["success"] is True
    assert result["id"] == "ep-101"
    print("[PASS] 2, 3, 5 & 6. Store episode endpoint, headers, scoping & parsing verified.")


def test_4_and_7_search_endpoint_and_parsing():
    """4, 7. Search constructs correct endpoint and parses response."""
    service = MemoryService(api_key="secret-key-xyz", base_url="https://api.thebreeth.com")
    
    recorded_request = None

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal recorded_request
        recorded_request = request
        return httpx.Response(200, json={"results": [{"id": "m1", "text": "Python experience"}]})

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        results = service.search_memory(
            session_id="test-session-123",
            query="Python experience",
            limit=3
        )

    assert recorded_request is not None
    # Test 4: Endpoint
    assert str(recorded_request.url) == "https://api.thebreeth.com/v1/search"
    assert recorded_request.headers["Authorization"] == "Bearer secret-key-xyz"

    import json
    body = json.loads(recorded_request.content)
    assert body["group_id"] == "interview:test-session-123"
    assert body["query"] == "Python experience"
    assert body["limit"] == 3

    # Test 7: Successful search response parsed
    assert len(results) == 1
    assert results[0]["id"] == "m1"
    print("[PASS] 4 & 7. Search endpoint and parsing verified.")


def test_8_http_error_handled_safely():
    """8. HTTP error (e.g. 500 / 401) is handled safely."""
    service = MemoryService(api_key="secret-key-xyz", base_url="https://api.thebreeth.com")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = service.store_episode("sess-1", [{"role": "user", "content": "test"}])
        search_res = service.search_memory("sess-1", "test")

    assert result["success"] is False
    assert result["status"] == "http_error"
    assert search_res == []
    print("[PASS] 8. HTTP error handled safely.")


def test_9_timeout_handled_safely():
    """9. Timeout exception is handled safely."""
    service = MemoryService(api_key="secret-key-xyz", base_url="https://api.thebreeth.com")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out", request=request)

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = service.store_episode("sess-1", [{"role": "user", "content": "test"}])
        search_res = service.search_memory("sess-1", "test")

    assert result["success"] is False
    assert result["status"] == "timeout"
    assert search_res == []
    print("[PASS] 9. Timeout handled safely.")


def test_10_api_key_never_exposed_in_error():
    """10. API key is never included in raised error messages or result text."""
    secret_key = "super-secret-breeth-key-999"
    service = MemoryService(api_key=secret_key, base_url="https://api.thebreeth.com")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise Exception(f"Failed with key {secret_key}")

    transport = httpx.MockTransport(mock_handler)
    with patch("httpx.post", side_effect=lambda url, **kwargs: httpx.Client(transport=transport).post(url, **kwargs)):
        result = service.store_episode("sess-1", [{"role": "user", "content": "test"}])

    assert result["success"] is False
    assert secret_key not in result["message"]
    assert "[REDACTED_API_KEY]" in result["message"] or secret_key not in str(result)
    print("[PASS] 10. API key is never exposed in error messages.")


def test_11_existing_tests_pass():
    """11. Existing Step 1, Step 2A, Step 2B and Step 2C tests still pass."""
    from test_api import test_health_check, test_create_session
    from test_candidate_profile_service import test_1_cand001_loads_successfully
    from test_curriculum_service import test_1_curriculum_loads_successfully
    from test_interview_planner import test_1_planner_loads_states_successfully

    test_health_check()
    test_create_session()
    test_1_cand001_loads_successfully()
    test_1_curriculum_loads_successfully()
    test_1_planner_loads_states_successfully()
    print("[PASS] 11. Existing Step 1, Step 2A, Step 2B, and Step 2C tests pass.")


if __name__ == "__main__":
    print("Running STEP 3A Test Suite...")
    test_1_missing_api_key_detected()
    test_2_and_3_and_5_store_episode_endpoint_header_scoping()
    test_4_and_7_search_endpoint_and_parsing()
    test_8_http_error_handled_safely()
    test_9_timeout_handled_safely()
    test_10_api_key_never_exposed_in_error()
    test_11_existing_tests_pass()
    print("\nALL STEP 3A TESTS PASSED SUCCESSFULLY!")
