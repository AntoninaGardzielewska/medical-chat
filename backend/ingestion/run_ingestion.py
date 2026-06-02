from backend.ingestion.chunk import ChunkArticles
from backend.ingestion.fetch import FetchArticles
from backend.ingestion.embed_and_store import ChromaDB
import json
import os

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, "articles.json")
    fetch_articles = FetchArticles(
        ["type 2 diabetes", "hypertension", "heart failure"], 1000, path
    )
    fetch_articles.get_articles()

    input_path = os.path.join(BASE_DIR, "articles.json")
    output_path = os.path.join(BASE_DIR, "chunked_articles.json")
    chunk_articles = ChunkArticles()
    chunk_articles.create_chunks(input_path, output_path, True)

    path_to_chroma = os.path.join(BASE_DIR, "../chroma_db/")
    path_to_data = os.path.join(BASE_DIR, "chunked_articles.json")

    chroma = ChromaDB(path_to_chroma, "pubmed_abstracts")
    chroma.add_file_data(path_to_data, verbose=True)

    print("\n--> Running verification search query...")
    results = chroma.get_item(query="diabetes treatment", n_results=3)
    print(json.dumps(results, indent=2))

