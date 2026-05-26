from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import os
class ChunkArticles:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size = 200,
            chunk_overlap = 20,
            length_function = len,
        )

    def chunk_article(self, article: dict) -> list[dict]:
        article_chunks = []
        text_chunks = self.splitter.split_text(article["article_text"])
        for text_chunk in text_chunks:
            new_article = article.copy()
            new_article["article_text"] = text_chunk
            article_chunks.append(new_article)
        return article_chunks

    def create_chunks(self, input_path: str, output_path: str, verbose: bool = False) -> None:
        chunks = []
        with open(input_path) as input_file:
            data = json.load(input_file)
            if verbose:
                print(f"Processing {len(data)} articles")
            for article in data:
                chunks += self.chunk_article(article)
        if verbose:
            print(f"Created {len(chunks)} chunks")
        with open(output_path, "w") as output_file:
            json.dump(chunks, output_file, indent=2)
        

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(BASE_DIR, "articles.json")
    output_path = os.path.join(BASE_DIR, "chunked_articles.json")
    chunk_articles = ChunkArticles()
    chunk_articles.create_chunks(input_path, output_path, True)