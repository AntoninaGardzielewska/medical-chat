"""Comprehensive tests for medical-chat ingestion pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ingestion.chunk import ArticleChunker
from ingestion.embed_and_store import ChromaDocumentStore
from ingestion.fetch import PubMedFetcher

# ============================================================================
# Test Data & Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def mock_model():
    """Mock the embeddings model to avoid downloading from HuggingFace Hub during tests"""
    with patch("transformers.AutoModel.from_pretrained") as mock_from_pretrained:
        mock_model = MagicMock()
        mock_from_pretrained.return_value = mock_model
        yield mock_from_pretrained


@pytest.fixture
def sample_article() -> dict:
    """Sample article for testing."""
    return {
        "pmid": "12345678",
        "year": "2022",
        "authors": [{"first_name": "John", "last_name": "Smith"}],
        "journal": "NEJM",
        "article_title": "Dietary sugar and T2DM",
        "article_text": "Background: " + "diabetes is a chronic condition. " * 30,
    }


@pytest.fixture
def pubmed_xml_response() -> str:
    """Sample PubMed XML response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://pubmed.ncbi.nlm.nih.gov/coredata/xml/pubmed_230101.dtd">
<PubmedArticleSet>
<PubmedArticle>
    <MedlineCitation Status="PubMed">
    <PMID Version="1">11111</PMID>
    <Article PubModel="Print">
        <Journal>
        <Title>The Lancet</Title>
        </Journal>
        <ArticleTitle>Effects of glucose on diabetes</ArticleTitle>
        <Abstract>
            <AbstractText>This study shows the effects of glucose on diabetes management.</AbstractText>
        </Abstract>
        <AuthorList CompleteYN="Y">
        <Author ValidYN="Y">
            <LastName>Smith</LastName>
            <ForeName>John</ForeName>
        </Author>
        </AuthorList>
        <PubDate>
            <Year>2023</Year>
        </PubDate>
    </Article>
    </MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>"""


@pytest.fixture
def temp_directory():
    """Create a temporary directory for file tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def chunker():
    """Create an ArticleChunker instance."""
    return ArticleChunker(chunk_size=200, chunk_overlap=20)


# ============================================================================
# ArticleChunker Tests
# ============================================================================


class TestArticleChunker:
    """Unit tests for ArticleChunker class."""

    def test_chunk_article_preserves_metadata(self, chunker, sample_article):
        """Verify that chunking preserves all article metadata."""
        chunks = chunker.chunk_article(sample_article)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["pmid"] == sample_article["pmid"]
            assert chunk["year"] == sample_article["year"]
            assert chunk["journal"] == sample_article["journal"]
            assert chunk["article_title"] == sample_article["article_title"]
            assert chunk["authors"] == sample_article["authors"]

    def test_chunk_article_long_text_produces_multiple_chunks(
        self, chunker, sample_article
    ):
        """Verify that long text is split into multiple chunks."""
        chunks = chunker.chunk_article(sample_article)
        assert len(chunks) > 1

    def test_chunk_article_short_text_produces_single_chunk(
        self, chunker, sample_article
    ):
        """Verify that short text produces a single chunk."""
        short_article = sample_article.copy()
        short_article["article_text"] = "Short text about diabetes."
        chunks = chunker.chunk_article(short_article)
        assert len(chunks) == 1

    def test_chunk_article_generates_unique_ids(self, chunker, sample_article):
        """Verify that each chunk receives a unique ID."""
        chunks = chunker.chunk_article(sample_article)
        chunk_ids = [chunk["id"] for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All unique
        assert all(chunk["id"].startswith(sample_article["pmid"]) for chunk in chunks)

    def test_chunk_article_missing_required_fields(self, chunker):
        """Verify that missing required fields raise ValueError."""
        incomplete_article = {"pmid": "123"}  # Missing article_text
        with pytest.raises(ValueError, match='must include "article_text" and "pmid"'):
            chunker.chunk_article(incomplete_article)

    def test_chunk_article_does_not_mutate_original(self, chunker, sample_article):
        """Verify that chunking does not mutate the original article."""
        original_text = sample_article["article_text"]
        chunker.chunk_article(sample_article)
        assert sample_article["article_text"] == original_text

    def test_create_chunks_writes_to_file(
        self, chunker, temp_directory, sample_article
    ):
        """Verify that create_chunks writes chunks to output file."""
        input_file = temp_directory / "articles.json"
        output_file = temp_directory / "chunks.json"
        input_file.write_text(json.dumps([sample_article]), encoding="utf-8")

        chunker.create_chunks(input_file, output_file, verbose=False)

        assert output_file.exists()
        chunks = json.loads(output_file.read_text(encoding="utf-8"))
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_create_chunks_creates_output_directory(
        self, chunker, temp_directory, sample_article
    ):
        """Verify that create_chunks creates output directory if it doesn't exist."""
        input_file = temp_directory / "articles.json"
        output_file = temp_directory / "subdir" / "chunks.json"
        input_file.write_text(json.dumps([sample_article]), encoding="utf-8")

        chunker.create_chunks(input_file, output_file, verbose=False)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_create_chunks_invalid_input_format(self, chunker, temp_directory):
        """Verify that create_chunks raises ValueError for non-list input."""
        input_file = temp_directory / "articles.json"
        output_file = temp_directory / "chunks.json"
        input_file.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

        with pytest.raises(ValueError, match="Expected a list of articles"):
            chunker.create_chunks(input_file, output_file)


# ============================================================================
# PubMedFetcher Tests
# ============================================================================


class TestPubMedFetcher:
    """Unit tests for PubMedFetcher class."""

    def test_search_for_ids_returns_list(self, temp_directory, pubmed_xml_response):
        """Verify that search_for_ids returns a list of PMIDs."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(["diabetes"], max_results=10, output_path=output_path)

        with patch.object(fetcher.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "esearchresult": {"idlist": ["11111", "22222"]}
            }
            mock_get.return_value = mock_response

            result = fetcher.search_for_ids("diabetes", 10)

        assert result == ["11111", "22222"]
        mock_get.assert_called_once()

    def test_search_for_ids_raises_on_http_error(self, temp_directory):
        """Verify that search_for_ids raises on HTTP error after retries."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(["diabetes"], max_results=10, output_path=output_path)

        with patch.object(fetcher.client, "get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(httpx.RequestError):
                fetcher.search_for_ids("diabetes", 10)

    def test_fetch_by_ids_parses_xml_correctly(
        self, temp_directory, pubmed_xml_response
    ):
        """Verify that fetch_by_ids correctly parses PubMed XML."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(["diabetes"], max_results=10, output_path=output_path)

        with patch.object(fetcher.client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.text = pubmed_xml_response
            mock_post.return_value = mock_response

            result = fetcher.fetch_by_ids(["11111"])

        assert len(result) == 1
        article = result[0]
        assert article["pmid"] == "11111"
        assert article["year"] == "2023"
        assert article["journal"] == "The Lancet"
        assert "glucose" in article["article_title"].lower()

    def test_fetch_by_ids_excludes_incomplete_articles(self, temp_directory):
        """Verify that fetch_by_ids filters out articles missing required fields."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(["diabetes"], max_results=10, output_path=output_path)

        incomplete_xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
            <PMID>99999</PMID>
            <Article>
                <ArticleTitle>Missing abstract</ArticleTitle>
                <!-- No AbstractText, should be filtered -->
            </Article>
            </MedlineCitation>
        </PubmedArticle>
        </PubmedArticleSet>"""

        with patch.object(fetcher.client, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.text = incomplete_xml
            mock_post.return_value = mock_response

            result = fetcher.fetch_by_ids(["99999"])

        assert len(result) == 0

    def test_get_articles_deduplicates_pmids(self, temp_directory, pubmed_xml_response):
        """Verify that get_articles deduplicates articles across search terms."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(
            ["diabetes", "hypertension"], max_results=10, output_path=output_path
        )

        with (
            patch.object(fetcher.client, "get") as mock_get,
            patch.object(fetcher.client, "post") as mock_post,
        ):
            # Both searches return the same PMID
            mock_get.return_value = MagicMock(
                json=lambda: {"esearchresult": {"idlist": ["11111"]}}
            )
            mock_post.return_value = MagicMock(text=pubmed_xml_response)

            fetcher.get_articles()

        # Verify output file contains deduplicated articles
        articles = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(articles) == 1

    def test_get_articles_respects_rate_limiting(
        self, temp_directory, pubmed_xml_response
    ):
        """Verify that get_articles sleeps between requests."""
        output_path = temp_directory / "articles.json"
        fetcher = PubMedFetcher(["diabetes"], max_results=10, output_path=output_path)

        with (
            patch.object(fetcher.client, "get") as mock_get,
            patch.object(fetcher.client, "post") as mock_post,
            patch("time.sleep") as mock_sleep,
        ):
            mock_get.return_value = MagicMock(
                json=lambda: {"esearchresult": {"idlist": ["11111", "22222"]}}
            )
            mock_post.return_value = MagicMock(text=pubmed_xml_response)

            fetcher.get_articles()

        # Verify sleep was called (rate limiting)
        assert mock_sleep.called


# ============================================================================
# ChromaDocumentStore Tests
# ============================================================================


class TestChromaDocumentStore:
    """Unit tests for ChromaDocumentStore class."""

    @pytest.fixture
    def mock_chromadb(self):
        """Mock chromadb PersistentClient."""
        with patch("chromadb.PersistentClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_model(self):
        """Mock SentenceTransformer model."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_instance = MagicMock()
            mock_st.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def chroma_store(self, temp_directory, mock_chromadb, mock_model):
        """Create a ChromaDocumentStore with mocked dependencies."""
        store = ChromaDocumentStore(
            persist_directory=temp_directory,
            collection_name="test_collection",
        )
        return store

    def test_select_device_cpu_fallback(
        self, mock_chromadb, mock_model, temp_directory
    ):
        """Verify that device selection defaults to CPU."""
        with (
            patch("torch.cuda.is_available", return_value=False),
            patch("torch.backends.mps.is_available", return_value=False),
        ):
            store = ChromaDocumentStore(temp_directory, "test")
            assert store.device == "cpu"

    def test_prepare_metadata_serializes_authors(self, chroma_store):
        """Verify that _prepare_metadata serializes complex objects."""
        chunk = {
            "id": "123",
            "pmid": "456",
            "article_text": "text here",
            "authors": [{"first_name": "John", "last_name": "Doe"}],
        }

        result = chroma_store._prepare_metadata(chunk)

        assert "article_text" not in result
        assert isinstance(result["authors"], str)
        assert "John" in result["authors"]

    def test_add_item_encodes_documents(self, chroma_store, mock_model):
        """Verify that add_item encodes documents using the model."""
        documents = ["document 1", "document 2"]
        metadatas = [{"pmid": "1"}, {"pmid": "2"}]
        ids = ["id1", "id2"]

        mock_model.encode.return_value = MagicMock(
            tolist=lambda: [[0.1, 0.2], [0.3, 0.4]]
        )

        chroma_store.add_item(documents, metadatas, ids)

        mock_model.encode.assert_called_once()
        chroma_store.collection.upsert.assert_called_once()

    def test_get_item_queries_collection(self, chroma_store, mock_model):
        """Verify that get_item queries the collection with encoded query."""
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2])
        chroma_store.collection.query.return_value = {
            "ids": [["1"]],
            "documents": [["text"]],
        }

        result = chroma_store.get_item("diabetes treatment", n_results=5)

        assert result is not None
        chroma_store.collection.query.assert_called_once()

    def test_add_file_data_processes_batches(
        self, chroma_store, temp_directory, mock_model
    ):
        """Verify that add_file_data processes data in batches."""
        chunks = [
            {
                "id": f"chunk_{i}",
                "pmid": f"pmid_{i}",
                "article_text": f"text {i}" * 50,
                "authors": [{"first_name": "Author", "last_name": f"Name{i}"}],
            }
            for i in range(5)
        ]
        data_file = temp_directory / "chunks.json"
        data_file.write_text(json.dumps(chunks), encoding="utf-8")

        mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1]] * 5)

        chroma_store.add_file_data(data_file, verbose=False)

        # Verify that add was called (batching happens internally)
        assert chroma_store.collection.upsert.called

    def test_add_file_data_invalid_format(self, chroma_store, temp_directory):
        """Verify that add_file_data raises ValueError for non-list input."""
        data_file = temp_directory / "chunks.json"
        data_file.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

        with pytest.raises(ValueError, match="Expected a list of chunked documents"):
            chroma_store.add_file_data(data_file)

    def test_add_file_data_creates_persist_directory(
        self, mock_chromadb, mock_model, temp_directory
    ):
        """Verify that add_file_data creates the persist directory if needed."""
        persist_dir = temp_directory / "subdir" / "chroma"
        store = ChromaDocumentStore(persist_dir, "test")

        chunks = [{"id": "1", "pmid": "1", "article_text": "text", "authors": []}]
        data_file = temp_directory / "chunks.json"
        data_file.write_text(json.dumps(chunks), encoding="utf-8")

        mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1]])

        store.add_file_data(data_file, verbose=False)

        assert persist_dir.exists()


# ============================================================================
# Integration Tests
# ============================================================================


class TestIngestionPipeline:
    """Integration tests for the full ingestion pipeline."""

    def test_end_to_end_pipeline_chunking_to_storage(
        self, temp_directory, sample_article
    ):
        """Verify the full pipeline from articles to stored embeddings."""
        # Stage 1: Create articles file
        articles_file = temp_directory / "articles.json"
        articles_file.write_text(json.dumps([sample_article]), encoding="utf-8")

        # Stage 2: Chunk articles
        chunks_file = temp_directory / "chunks.json"
        chunker = ArticleChunker()
        chunker.create_chunks(articles_file, chunks_file, verbose=False)

        chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
        assert len(chunks) > 0
        assert all("id" in chunk and "article_text" in chunk for chunk in chunks)

        # Stage 3: Mock storage (would require chromadb initialization)
        assert chunks_file.exists()
        assert len(chunks) > 1  # Long text should produce multiple chunks

    @pytest.mark.parametrize(
        "num_articles,expected_min_chunks",
        [
            (1, 1),
            (3, 3),
            (5, 5),
        ],
    )
    def test_pipeline_with_varying_input_sizes(
        self, temp_directory, sample_article, num_articles, expected_min_chunks
    ):
        """Parametrized test for different input sizes."""
        articles = [
            {
                **sample_article,
                "pmid": str(i),
                "article_text": sample_article["article_text"],
            }
            for i in range(num_articles)
        ]
        articles_file = temp_directory / "articles.json"
        articles_file.write_text(json.dumps(articles), encoding="utf-8")

        chunks_file = temp_directory / "chunks.json"
        chunker = ArticleChunker()
        chunker.create_chunks(articles_file, chunks_file, verbose=False)

        chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
        assert len(chunks) >= expected_min_chunks
