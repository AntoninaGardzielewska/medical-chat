from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("neuml/pubmedbert-base-embeddings")


class ArticleChunker:
    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 32) -> None:

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda text: len(tokenizer.encode(text)),
        )

    def chunk_article(self, article: dict[str, Any]) -> list[dict[str, Any]]:
        article_text = article.get("article_text")
        pmid = article.get("pmid")
        if not article_text or not pmid:
            raise ValueError('Article must include "article_text" and "pmid"')

        chunks: list[dict[str, Any]] = []
        text_chunks = self.splitter.split_text(article_text)
        for idx, text_chunk in enumerate(text_chunks):
            chunk_data = article.copy()
            chunk_data["article_text"] = text_chunk
            chunk_data["id"] = f"{pmid}_{idx}"
            chunks.append(chunk_data)
        return chunks

    def create_chunks(
        self,
        input_path: Path | str,
        output_path: Path | str,
        verbose: bool = False,
    ) -> None:
        input_path = Path(input_path)
        output_path = Path(output_path)

        with input_path.open("r", encoding="utf-8") as input_file:
            data = json.load(input_file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of articles in the input file")

        if verbose:
            print(f"Processing {len(data)} articles")

        chunks: list[dict[str, Any]] = []
        for article in data:
            chunks.extend(self.chunk_article(article))

        if verbose:
            print(f"Created {len(chunks)} chunks")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(chunks, output_file, indent=2)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "articles.json"
    output_path = base_dir / "chunked_articles.json"

    chunker = ArticleChunker()
    chunker.create_chunks(input_path, output_path, verbose=True)


if __name__ == "__main__":
    main()
