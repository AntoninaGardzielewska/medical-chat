from __future__ import annotations

import json
import random
from pathlib import Path

from ingestion.embed_and_store import ChromaDocumentStore


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    chroma_dir = base_dir.parent / "chroma_db"

    print("--> Connecting to ChromaDB...")
    store = ChromaDocumentStore(chroma_dir, "pubmed_abstracts")
    collection = store.collection

    # ── 1. Total chunk count ──────────────────────────────────────
    print_section("1. TOTAL CHUNKS IN DATABASE")
    total = collection.count()
    print(f"  Total chunks stored: {total:,}")

    # ── 2. Random sample of 5 chunks ─────────────────────────────
    print_section("2. RANDOM SAMPLE (5 chunks)")

    # ChromaDB doesn't have a native "random" fetch, so we:
    # - get all IDs, pick 5 at random, then fetch those specifically
    all_ids_result = collection.get(include=[])          # only returns ids
    all_ids = all_ids_result["ids"]

    sample_ids = random.sample(all_ids, min(5, len(all_ids)))
    sample = collection.get(ids=sample_ids, include=["documents", "metadatas"])

    for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"]), 1):
        print(f"\n  --- Chunk {i} ---")
        print(f"  PMID    : {meta.get('pmid', 'N/A')}")
        print(f"  Title   : {meta.get('article_title', 'N/A')}")
        print(f"  Journal : {meta.get('journal', 'N/A')}")
        print(f"  Year    : {meta.get('year', 'N/A')}")
        # Truncate long text for readability
        preview = doc[:200] + "..." if len(doc) > 200 else doc
        print(f"  Text    : {preview}")

    # ── 3. Semantic search test ───────────────────────────────────
    print_section("3. SEMANTIC SEARCH TEST")
    test_query = "treatment options for type 2 diabetes"
    print(f"  Query: '{test_query}'")
    print()

    results = store.get_item(query=test_query, n_results=5)

    ids       = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc_id, doc, meta, dist) in enumerate(
        zip(ids, documents, metadatas, distances), 1
    ):
        print(f"  Result {i}  (distance: {dist:.4f})")
        print(f"  ID      : {doc_id}")
        print(f"  PMID    : {meta.get('pmid', 'N/A')}")
        print(f"  Title   : {meta.get('article_title', 'N/A')}")
        preview = doc[:200] + "..." if len(doc) > 200 else doc
        print(f"  Text    : {preview}")
        print()


if __name__ == "__main__":
    main()