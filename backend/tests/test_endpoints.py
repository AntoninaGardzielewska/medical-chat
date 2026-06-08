"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_chat_placeholder(client: TestClient) -> None:
    payload = {
        "question": "Hello",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "disclaimer" in data
    assert isinstance(data["disclaimer"], str)

    assert "answer" in data
    assert isinstance(data["answer"], str)

    assert "references" in data
    assert isinstance(data["references"], list)


def test_chat_empty_question(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"question": ""},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Question cannot be empty"


def test_chat_with_session_id(client: TestClient) -> None:
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "session_id": "test-session-123",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
