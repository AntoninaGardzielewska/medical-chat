"""Tests for API endpoints."""

from unittest.mock import patch

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


@patch("rag.llm.OllamaChat.ask_llm")
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
