from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Suppress multi-processing bugs and parallel tokenization deadlocks
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
import torch
from sentence_transformers import SentenceTransformer


class ChromaDocumentStore:
    def __init__(
        self,
        persist_directory: Path | str,
        collection_name: str,
        model_name: str = "neuml/pubmedbert-base-embeddings",
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.model_name = model_name
        self.device = self._select_device()

        print(f"--> Initializing {self.model_name} on device: {self.device.upper()}")
        self.model = SentenceTransformer(self.model_name, device=self.device)

        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def _select_device(self) -> str:
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _prepare_metadata(self, chunk: dict[str, Any]) -> dict[str, Any]:
        metadata = {k: v for k, v in chunk.items() if k != "article_text"}
        authors = metadata.get("authors")
        if authors is not None and not isinstance(authors, (str, int, float, bool)):
            metadata["authors"] = json.dumps(authors)
        return metadata

    def add_item(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        embeddings = self.model.encode(
            documents,
            batch_size=16,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()

        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids,
        )

    def get_item(self, query: str, n_results: int) -> Any:
        encoded_query = self.model.encode(query, convert_to_numpy=True).tolist()
        results = self.collection.query(
            query_embeddings=[encoded_query], n_results=n_results
        )
        return results

    def add_file_data(self, path: Path | str, verbose: bool = False) -> None:
        path = Path(path)
        with path.open("r", encoding="utf-8") as input_file:
            data = json.load(input_file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of chunked documents")

        total_records = len(data)
        batch_size = 32

        print(f"--> Found {total_records} documents inside {path.name}")
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        for i in range(0, total_records, batch_size):
            batch_chunks = data[i : i + batch_size]

            if verbose:
                print(
                    f" Processing batch {i // batch_size + 1}: documents {i} to {min(i + batch_size, total_records) - 1}..."
                )

            documents = [chunk["article_text"] for chunk in batch_chunks]
            ids = [chunk["id"] for chunk in batch_chunks]
            metadatas = [self._prepare_metadata(chunk) for chunk in batch_chunks]

            self.add_item(documents, metadatas, ids)

            if verbose and (
                (i + len(batch_chunks)) % 500 == 0
                or i + len(batch_chunks) == total_records
            ):
                print(
                    f" [PROGRESS] Total stored successfully so far: {i + len(batch_chunks)} documents"
                )


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    path_to_chroma = base_dir.parent / "chroma_db"
    path_to_data = base_dir / "chunked_articles.json"

    chroma_store = ChromaDocumentStore(path_to_chroma, "pubmed_abstracts")
    chroma_store.add_file_data(path_to_data, verbose=True)

    print("\n--> Running verification search query...")
    results = chroma_store.get_item(query="diabetes treatment", n_results=3)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
