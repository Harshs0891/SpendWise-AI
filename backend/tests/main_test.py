from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_success():
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_check_returns_expected_data():
    response = client.get("/api/v1/health")

    assert response.json() == {
        "status": "healthy",
        "application": "SpendWise AI",
    }