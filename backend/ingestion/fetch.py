import json
import time
import xml.etree.ElementTree as ET
import functools
import httpx
import os
def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except httpx.RequestError:
                if attempt == 2:
                    raise
                time.sleep(1)
    return wrapper

class FetchArticles:
    def __init__(self, terms: list[str], no_articles: int, path_to_results: str):
        self.terms = terms
        self.no_articles = no_articles
        self.path_to_results = path_to_results
                
    @retry
    def search_for_ids(self, term: str, max_results: int) -> list[str]:
        response = httpx.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": term,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
        )

        return response.json()["esearchresult"]["idlist"]

    @retry
    def fetch_by_ids(self, ids: list[str]) -> list[dict]:
        def safe_text(node, search):
            if node is None:
                return None
            result = node.find(search)
            return result.text if result is not None else None

        response = httpx.post(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
        )
        articles = []
        root = ET.fromstring(response.text)
        for article in root.findall(".//PubmedArticle"):
            pmid = safe_text(article, ".//PMID")
            year = safe_text(article, ".//Year")
            article_title = safe_text(article, ".//ArticleTitle")
            text = safe_text(article, ".//AbstractText")
            journal = safe_text(article, ".//Journal/Title")
            authors = []
            for author in article.findall(".//Author"):
                last_name = safe_text(author, ".//LastName")
                first_name = safe_text(author, ".//ForeName")
                authors.append({"first_name": first_name, "last_name": last_name})
            if all([pmid, year, article_title, text]):
                articles.append(
            
                    {
                        "pmid": pmid,
                        "year": year,
                        "authors": authors,
                        "journal": journal,
                        "article_title": article_title,
                        "article_text": text,
                    }
                )
        return articles

    def get_articles(self) -> None:
        articles = []
        seen_pmids = set()
        for term in self.terms:
            ids = self.search_for_ids(term, self.no_articles)
            for batch in range(0, len(ids), 200):
                articles_batch = self.fetch_by_ids(ids[batch : batch + 200])
                for article in articles_batch:
                    if article["pmid"] not in seen_pmids:
                        seen_pmids.add(article["pmid"])
                        articles.append(article)
                time.sleep(0.4)
        with open(self.path_to_results, "w") as file:
            json.dump(articles, file, indent=2)
        return


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, "articles.json")
    fetch_articles = FetchArticles(["type 2 diabetes", "hypertension", "heart failure"], 1000, path)
    fetch_articles.get_articles()
