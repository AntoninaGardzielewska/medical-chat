from unittest.mock import patch

from rag.retrieve import retrieve


class FakeChromaStore:
    def __init__(self, result):
        self._result = result

    def get_item(self, query: str, n_results: int):
        return self._result

def test_retrieve_returns_empty_when_no_similar_candidates():
    fake_result = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [[
            {"pmid": "1", "article_title": "A", "authors": '[]', "journal": "J1", "year": "2024"},
            {"pmid": "2", "article_title": "B", "authors": '[]', "journal": "J2", "year": "2023"},
        ]],
        "distances": [[0.60, 0.55]],
    }

    with patch("rag.retrieve._get_chroma_store", return_value=FakeChromaStore(fake_result)):
        results = retrieve("test query", max_results=10, max_distance=0.35)

    assert results == []
