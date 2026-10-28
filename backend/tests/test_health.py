"""
Smoke test for the /health endpoint.

Uses FastAPI's built-in test client (backed by httpx) so we don't need
to start the real server. This pattern is standard for FastAPI projects.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "civicshield-backend"

