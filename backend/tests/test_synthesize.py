from rag.synthesize import _build_references, _extract_citation_numbers


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
