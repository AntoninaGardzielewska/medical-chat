from __future__ import annotations

import functools
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx


def retry(max_attempts: int = 3, delay_seconds: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError, ET.ParseError):
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay_seconds)
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper

    return decorator


class PubMedFetcher:
    def __init__(
        self, terms: list[str], max_results: int, output_path: Path | str
    ) -> None:
        self.terms = terms
        self.max_results = max_results
        self.output_path = Path(output_path)
        self.client = httpx.Client(timeout=10.0)

    @retry()
    def search_for_ids(self, term: str, max_results: int) -> list[str]:
        response = self.client.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": term,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["esearchresult"]["idlist"]

    @retry()
    def fetch_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        def safe_text(node: ET.Element | None, search: str) -> str | None:
            if node is None:
                return None
            result = node.find(search)
            return result.text if result is not None else None

        response = self.client.post(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
        )
        response.raise_for_status()

        root = ET.fromstring(response.text)
        articles: list[dict[str, Any]] = []
        for article in root.findall(".//PubmedArticle"):
            pmid = safe_text(article, ".//PMID")
            year = safe_text(article, ".//Year")
            article_title = safe_text(article, ".//ArticleTitle")
            text = safe_text(article, ".//AbstractText")
            journal = safe_text(article, ".//Journal/Title")
            authors: list[dict[str, str | None]] = []
            for author in article.findall(".//Author"):
                authors.append(
                    {
                        "first_name": safe_text(author, ".//ForeName"),
                        "last_name": safe_text(author, ".//LastName"),
                    }
                )
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

    def get_articles(self) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        seen_pmids: set[str] = set()

        for term in self.terms:
            ids = self.search_for_ids(term, self.max_results)
            for batch_start in range(0, len(ids), 200):
                batch_ids = ids[batch_start : batch_start + 200]
                articles_batch = self.fetch_by_ids(batch_ids)
                for article in articles_batch:
                    pmid = article["pmid"]
                    if pmid not in seen_pmids:
                        seen_pmids.add(pmid)
                        articles.append(article)
                time.sleep(0.4)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as file:
            json.dump(articles, file, indent=2)
        return articles


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / "articles.json"
    fetcher = PubMedFetcher(
        terms=["type 2 diabetes", "hypertension", "heart failure"],
        max_results=1000,
        output_path=output_path,
    )
    fetcher.get_articles()


if __name__ == "__main__":
    main()
