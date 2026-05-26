from unittest.mock import MagicMock, patch

from ingestion.fetch import FetchArticles


class TestSearchIds:
    xml_text = """
        <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
            <PMID>11111</PMID>
            <Article>
                <Journal><Title>The Lancet</Title></Journal>
                <ArticleTitle>Effects of glucose on diabetes</ArticleTitle>
                <Abstract><AbstractText>This study shows...</AbstractText></Abstract>
                <AuthorList>
                <Author>
                    <LastName>Smith</LastName>
                    <ForeName>John</ForeName>
                </Author>
                </AuthorList>
            </Article>
            <PubDate><Year>2023</Year></PubDate>
            </MedlineCitation>
        </PubmedArticle>
        </PubmedArticleSet>
    """

    def test_returns_list_of_ids(self):
        fetcher = FetchArticles(["diabetes"], 10, "./test_output.json")

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                json=lambda: {"esearchresult": {"idlist": ["11111", "22222", "33333"]}}
            )

            result = fetcher.search_for_ids("diabetes", 10)
        assert result == ["11111", "22222", "33333"]

    def test_fetch_ids_returns_list_of_dicts(self):
        fetcher = FetchArticles(["diabetes"], 10, "./test_output.json")

        with patch("httpx.post") as mock_post:
            mock_post.return_value = MagicMock(text=self.xml_text)
            result = fetcher.fetch_by_ids(["11111"])
            assert result == [
                {
                    "pmid": "11111",
                    "year": "2023",
                    "authors": [{"first_name": "John", "last_name": "Smith"}],
                    "journal": "The Lancet",
                    "article_title": "Effects of glucose on diabetes",
                    "article_text": "This study shows...",
                }
            ]

    def test_get_articles_deduplicates(self):
        fetcher = FetchArticles(["diabetes", "hypertension"], 10, "./test_output.json")

        with (
            patch("httpx.get") as mock_get,
            patch("httpx.post") as mock_post,
            patch("json.dump") as mock_dump,
        ):
            mock_get.return_value = MagicMock(
                json=lambda: {"esearchresult": {"idlist": ["11111"]}}
            )
            mock_post.return_value = MagicMock(text=self.xml_text)

            fetcher.get_articles()

            args, kwargs = mock_dump.call_args
            saved_articles = args[0]
            assert len(saved_articles) == 1
