import json
import logging
import time
from pathlib import Path

from ingestion.embed_and_store import ChromaDocumentStore

logger = logging.getLogger(__name__)
base_dir = Path(__file__).resolve().parent
path_to_chroma = base_dir.parent / "chroma_db"

_chroma_document = None


def _get_chroma_store():
    """Lazy initialization of ChromaDocumentStore."""
    global _chroma_document
    if _chroma_document is None:
        start = time.perf_counter()
        _chroma_document = ChromaDocumentStore(path_to_chroma, "pubmed_abstracts")
        duration = time.perf_counter() - start
        logger.info("ChromaDocumentStore initialized in %.3f s", duration)
    return _chroma_document


def retrieve(
    query: str,
    max_results: int = 20,
    max_distance: float = 200.0,
) -> list[dict]:
    """Retrieve the most relevant chunks for a query.

    We request a larger candidate set from Chroma and then filter by a
    distance threshold to avoid returning weakly related matches. The final
    response contains at most `max_results` chunks, but may be fewer if few candidates
    pass the similarity threshold.
    """

    start = time.perf_counter()
    chroma = _get_chroma_store()
    output = chroma.get_item(query, max_results)
    duration = time.perf_counter() - start

    documents = output["documents"][0]
    metadatas = output["metadatas"][0]
    distances = output["distances"][0]
    logger.info(
        "retrieve(query=%r, max_results=%d, max_distance=%.3f) completed in %.3f s (candidates=%d)",
        query,
        max_results,
        max_distance,
        duration,
        len(documents),
    )

    scored_results = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=True):
        if dist is None:
            continue
        if dist > max_distance:
            continue

        scored_results.append(
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

    scored_results.sort(key=lambda item: item["distance"])
    selected = scored_results[:max_results]

    logger.info(
        "retrieve filtered to %d results after similarity threshold",
        len(selected),
    )
    return selected


if __name__ == "__main__":
    import pprint

    queries = [
        "what is hypertension?",
        "treatment options for type 2 diabetes",
        "symptoms of heart failure",
        "i love dogs",
    ]
    for q in queries:
        start = time.time()
        print(f"\n=== Query: {q} ===")
        pprint.pprint(retrieve(q))
        end = time.time()
        print(f"Time: {end - start:.3f}s")
