import json
import os
import sys
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from services.session_manager import session_manager

client = TestClient(app)


def test_health_check():
    """Verify GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {"status": "ok"}, f"Unexpected payload: {response.json()}"
    print("[PASS] GET /health works successfully.")


def test_create_session():
    """Verify POST /api/interview with candidate creates a new session."""
    session_manager.clear_all()
    payload = {
        "sessionId": "test-session-101",
        "candidate": {
            "member": {
                "id": "CAND-001",
                "name": "Sarah Johnson",
                "jobRole": "Senior Data Engineer"
            }
        }
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["reply"] == "Welcome. Let's begin your interview.", f"Unexpected reply: {data['reply']}"
    assert data["done"] is False
    assert session_manager.session_exists("test-session-101")
    print("[PASS] POST /api/interview with candidate creates session successfully.")


def test_subsequent_message():
    """Verify POST /api/interview with existing session retrieves state and responds."""
    payload = {
        "sessionId": "test-session-101",
        "message": "I have experience with Python and distributed systems."
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["reply"] == "Response received. Interview processing will be implemented in the next step."
    assert data["done"] is False
    
    session = session_manager.get_session("test-session-101")
    assert len(session["conversation"]) == 1
    assert session["conversation"][0]["content"] == "I have experience with Python and distributed systems."
    print("[PASS] POST /api/interview with existing sessionId + message retrieves session successfully.")


def test_nonexistent_session_404():
    """Verify POST /api/interview with new sessionId + message returns 404."""
    payload = {
        "sessionId": "unknown-session-999",
        "message": "Hello?"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    print("[PASS] POST /api/interview with missing sessionId returns 404 as expected.")


def test_empty_session_id_validation():
    """Verify empty sessionId fails validation."""
    payload = {
        "sessionId": "   ",
        "message": "Hello"
    }
    response = client.post("/api/interview", json=payload)
    assert response.status_code in (400, 422), f"Expected 400 or 422, got {response.status_code}"
    print("[PASS] Empty sessionId validation works as expected.")


if __name__ == "__main__":
    print("Running Step 1 Backend API Tests...")
    test_health_check()
    test_create_session()
    test_subsequent_message()
    test_nonexistent_session_404()
    test_empty_session_id_validation()
    print("\nALL STEP 1 TESTS PASSED SUCCESSFULLY!")
