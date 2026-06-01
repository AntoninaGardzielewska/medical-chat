from sentence_transformers import SentenceTransformer
import chromadb
import json

class ChromaDB:
    def __init__(self, collection_name):
        self.model = SentenceTransformer("neuml/pubmedbert-base-embeddings")

        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=self.model) 

    def add_item(self, documents, metadatas, ids):
        self.collection.add(
            documents = documents,
            metadatas = metadatas,
            ids = ids
        )

    def get_item(self, query, n_results):
        results = self.collection.query(
            query_texts=query,
            n_results=n_results
        )

        return results

    def add_file_data(self, path: str, verbose: bool = False):
        with open(path) as input_file:
            data = json.load(input_file)
            idx = 1
            for chunk in data:
                document = chunk["article_text"]
                metadata = chunk.copy()
                metadata.pop("article_text")
                id = chunk["id"]
                self.add_item(document, metadata, id)
                if verbose and idx % 100 == 0:
                    print(f"processed: {idx} documents")

