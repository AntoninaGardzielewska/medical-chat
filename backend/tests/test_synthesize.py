from unittest.mock import patch

from rag.synthesize import _build_references, _extract_citation_numbers, synthesize


def test_extract_citation_numbers() -> None:
    answer = "Impaired insulin release and sensitivity [1] and insulin resistance [2]."
    assert _extract_citation_numbers(answer) == {1, 2}


def test_build_references_filters_only_cited_sources() -> None:
    chunks = [
        {
            "pmid": "11111111",
            "title": "Study One",
            "authors": [],
            "journal": "Journal A",
            "year": "2023",
            "text": "",
        },
        {
            "pmid": "22222222",
            "title": "Study Two",
            "authors": [],
            "journal": "Journal B",
            "year": "2024",
            "text": "",
        },
    ]

    references = _build_references(chunks, {2})

    assert len(references) == 1
    assert references[0]["number"] == 2
    assert references[0]["pmid"] == "22222222"


@patch("rag.synthesize.OllamaChat.ask_llm")
def test_synthesize_returns_only_cited_references(mock_ask_llm) -> None:
    mock_ask_llm.return_value = '{"answer": "High blood sugar is caused by impaired insulin release [1]."}'

    chunks = [
        {
            "pmid": "11111111",
            "title": "Study One",
            "authors": [],
            "journal": "Journal A",
            "year": "2023",
            "text": "Text 1",
        },
        {
            "pmid": "22222222",
            "title": "Study Two",
            "authors": [],
            "journal": "Journal B",
            "year": "2024",
            "text": "Text 2",
        },
    ]

    result = synthesize("What causes high blood sugar?", chunks)

    assert result["answer"] == "High blood sugar is caused by impaired insulin release ."
    assert result["include_sources"] is True
    assert len(result["references"]) == 1
    assert result["references"][0]["number"] == 1


@patch("rag.synthesize.OllamaChat.ask_llm")
def test_synthesize_parses_json_with_trailing_comma(mock_ask_llm) -> None:
    mock_ask_llm.return_value = '{"answer": "High blood sugar is caused by impaired insulin release [1].", }'

    chunks = [
        {
            "pmid": "11111111",
            "title": "Study One",
            "authors": [],
            "journal": "Journal A",
            "year": "2023",
            "text": "Text 1",
        },
    ]

    result = synthesize("What causes high blood sugar?", chunks)

    assert result["answer"] == "High blood sugar is caused by impaired insulin release [1]."
    assert result["include_sources"] is True
    assert len(result["references"]) == 1
    assert result["references"][0]["number"] == 1
