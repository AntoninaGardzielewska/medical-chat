import json
from pathlib import Path

from ingestion.embed_and_store import ChromaDocumentStore

base_dir = Path(__file__).resolve().parent
path_to_chroma = base_dir.parent / "chroma_db"

_chroma_document = None


def _get_chroma_store():
    """Lazy initialization of ChromaDocumentStore."""
    global _chroma_document
    if _chroma_document is None:
        _chroma_document = ChromaDocumentStore(path_to_chroma, "pubmed_abstracts")
    return _chroma_document


def retrieve(query: str, k: int = 5) -> list[dict]:
    chroma = _get_chroma_store()
    output = chroma.get_item(query, k)

    documents = output["documents"][0]
    metadatas = output["metadatas"][0]
    distances = output["distances"][0]

    results = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=True):
        results.append(
            {
                "text": doc,
                "pmid": meta["pmid"],
                "title": meta["article_title"],
                "authors": json.loads(meta["authors"]),
                "journal": meta["journal"],
                "year": meta["year"],
                "distance": dist,
            }
        )

    return results


if __name__ == "__main__":
    import pprint
    import time

    queries = [
        "what is hypertension?",
        "treatment options for type 2 diabetes",
        "symptoms of heart failure",
    ]
    for q in queries:
        start = time.time()
        print(f"\n=== Query: {q} ===")
        pprint.pprint(retrieve(q, k=3))
        end = time.time()
        print(f"Time: {end - start}")
