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


@patch("src.routers.chat.synthesize")
@patch("src.routers.chat.retrieve")
@patch("src.routers.chat.rewrite_query")
def test_chat_success(
    mock_rewrite,
    mock_retrieve,
    mock_synthesize,
    client: TestClient,
) -> None:
    mock_rewrite.return_value = "rewritten clinical query"
    mock_retrieve.return_value = [
        {
            "text": "Example medical evidence",
            "pmid": "12345678",
        }
    ]

    mock_synthesize.return_value = {
        "disclaimer": (
            "This information is for educational purposes only "
            "and is not medical advice."
        ),
        "answer": "Mocked medical answer.",
        "references": [
            {
                "number": 1,
                "pmid": "12345678",
                "title": "Example Study",
                "authors": "Smith et al.",
                "journal": "Medical Journal",
                "year": "2024",
                "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            }
        ],
    }

    response = client.post(
        "/api/v1/chat",
        json={"question": "Does sugar cause diabetes?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "Mocked medical answer."
    assert len(data["references"]) == 1
    assert data["references"][0]["pmid"] == "12345678"

    mock_rewrite.assert_called_once_with("Does sugar cause diabetes?")
    mock_retrieve.assert_called_once()
    mock_synthesize.assert_called_once()


def test_chat_empty_question(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"question": ""},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Question cannot be empty"


def test_chat_missing_question(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={},
    )

    assert response.status_code == 422
