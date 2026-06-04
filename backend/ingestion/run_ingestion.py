from __future__ import annotations

import json
from pathlib import Path

from ingestion.chunk import ArticleChunker
from ingestion.embed_and_store import ChromaDocumentStore
from ingestion.fetch import PubMedFetcher


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    articles_path = base_dir / "articles.json"
    chunked_path = base_dir / "chunked_articles.json"
    chroma_dir = base_dir.parent / "chroma_db"

    terms = ["type 2 diabetes", "hypertension", "heart failure"]
    fetcher = PubMedFetcher(
        terms=terms,
        max_results=1000,
        output_path=articles_path,
    )
    print(f"--> Fetching articles for: {terms}")
    fetcher.get_articles()
    print(f"--> Saved raw articles to {articles_path}")

    chunker = ArticleChunker()
    chunker.create_chunks(articles_path, chunked_path, verbose=True)

    chroma_store = ChromaDocumentStore(chroma_dir, "pubmed_abstracts")
    chroma_store.add_file_data(chunked_path, verbose=True)

    print(f"--> Articles saved to: {articles_path}")
    print(f"--> Chunks saved to:   {chunked_path}")

    print("\n--> Running verification search query...")
    results = chroma_store.get_item(query="diabetes treatment", n_results=3)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
