import sys
from pathlib import Path

# Add root directory to path so tests can import src modules
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from fastapi.testclient import TestClient
from src.api.main import app
from src.config import settings

client = TestClient(app)
API_KEY = settings.API_SECRET_KEY

def test_health_check():
    """Verify health check endpoint returns 200 and correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "support-resolution-desk"

def test_webhook_unauthorized():
    """Verify that calling webhook without X-API-Key header returns 403 Forbidden."""
    response = client.post(
        "/webhook/email",
        json={
            "raw_email_text": "Where is my order?",
            "sender_email": "test@example.com",
            "subject": "Status",
            "thread_id": "test_unauth"
        }
    )
    assert response.status_code == 403

def test_webhook_authorized_success():
    """Verify that calling webhook with correct X-API-Key processes successfully."""
    headers = {"X-API-Key": API_KEY}
    payload = {
        "raw_email_text": "Where is my order #12345? Can you send me tracking info?",
        "sender_email": "customer@example.com",
        "subject": "Order Status Inquiry",
        "thread_id": "test_auth_001"
    }
    response = client.post("/webhook/email", json=payload, headers=headers)
    
    # Depending on model speed or mocking, it should return 200 OK
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "category" in data
    assert "final_output" in data