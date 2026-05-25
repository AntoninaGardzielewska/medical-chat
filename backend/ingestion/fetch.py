import json
import time
import xml.etree.ElementTree as ET

import httpx


class FetchArticles:
    def __init__(self, terms: list[str], no_articles: int, path_to_results: str):
        self.terms = terms
        self.no_articles = no_articles
        self.path_to_results = path_to_results

    def search_for_ids(self, term: str, max_results: int) -> list[int]:
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

    def fetch_by_ids(self, ids: list[int]):
        def safe_text(node):
            return node.text if node is not None else None

        response = httpx.post(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
        )
        articles = []
        root = ET.fromstring(response.text)
        for article in root.findall(".//PubmedArticle"):
            pmid = safe_text(article.find(".//PMID"))
            year = safe_text(article.find(".//Year"))
            article_title = safe_text(article.find(".//ArticleTitle"))
            text = safe_text(article.find(".//AbstractText"))
            authors = []
            for author in article.findall(".//Author"):
                last_name = safe_text(author.find(".//LastName"))
                first_name = safe_text(author.find(".//ForeName"))
                authors.append({"first_name": first_name, "last_name": last_name})

            articles.append(
                {
                    "pmid": pmid,
                    "year": year,
                    "article_title": article_title,
                    "article_text": text,
                    "authors": authors,
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
    fetch_articles = FetchArticles(["glucose"], 10, "./backend/ingestion/articles.json")
    fetch_articles.get_articles()
