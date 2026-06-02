import os

# Suppress multi-processing bugs and parallel tokenization deadlocks
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json

import chromadb
import torch
from sentence_transformers import SentenceTransformer


class ChromaDB:
    def __init__(self, path: str, collection_name: str):
        # Correctly check PyTorch for hardware acceleration
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

        print(f"--> Initializing PubMedBERT on device: {device.upper()}")
        self.model = SentenceTransformer(
            "neuml/pubmedbert-base-embeddings", device=device
        )

        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_item(self, documents, metadatas, ids) -> None:
        # Convert text array directly into embeddings using a safe model batch size
        embeddings = self.model.encode(
            documents, batch_size=16, show_progress_bar=False, convert_to_numpy=True
        ).tolist()

        self.collection.add(
            documents=documents, metadatas=metadatas, embeddings=embeddings, ids=ids
        )

    def get_item(self, query: str, n_results: int):
        encoded_query = self.model.encode(query, convert_to_numpy=True).tolist()
        results = self.collection.query(
            query_embeddings=encoded_query, n_results=n_results
        )
        return results

    def add_file_data(self, path: str, verbose: bool = False) -> None:
        with open(path) as input_file:
            data = json.load(input_file)

        total_records = len(data)
        batch_size = 32

        print(f"--> Found {total_records} documents inside {os.path.basename(path)}")

        for i in range(0, total_records, batch_size):
            batch_chunks = data[i : i + batch_size]

            if verbose:
                print(
                    f" Processing batch {i // batch_size + 1}: documents {i} to {min(i + batch_size, total_records)}..."
                )

            documents = [chunk["article_text"] for chunk in batch_chunks]
            ids = [chunk["id"] for chunk in batch_chunks]

            # Safely isolate metadata without nested arrays/dicts mutating originals
            metadatas = []
            for chunk in batch_chunks:
                meta = {k: v for k, v in chunk.items() if k != "article_text"}

                # Turn any remaining nested dictionary/list data (like authors) into a queryable string
                if "authors" in meta and not isinstance(
                    meta["authors"], (str, int, float, bool)
                ):
                    meta["authors"] = json.dumps(meta["authors"])

                metadatas.append(meta)

            self.add_item(documents, metadatas, ids)

            if verbose and i > 0 and i % 500 < batch_size:
                print(f" [PROGRESS] Total stored successfully so far: {i} documents")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path_to_chroma = os.path.join(BASE_DIR, "../chroma_db/")
    path_to_data = os.path.join(BASE_DIR, "chunked_articles.json")

    chroma = ChromaDB(path_to_chroma, "pubmed_abstracts")
    chroma.add_file_data(path_to_data, verbose=True)

    print("\n--> Running verification search query...")
    results = chroma.get_item(query="diabetes treatment", n_results=3)
    print(json.dumps(results, indent=2))
