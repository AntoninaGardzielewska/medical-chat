"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

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


@patch("src.rag.llm.OllamaChat.__call__")  # Mock the Ollama call
def test_chat_placeholder(mock_ollama, client: TestClient) -> None:
    mock_ollama.return_value = "Mocked response to your question."
    
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


@patch("src.rag.llm.OllamaChat.__call__")  # Mock the Ollama call
def test_chat_with_session_id(mock_ollama, client: TestClient) -> None:
    mock_ollama.return_value = "Mocked response to your message."
    
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "session_id": "test-session-123",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"