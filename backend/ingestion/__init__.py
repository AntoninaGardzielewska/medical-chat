from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from .embed_and_store import ChromaDocumentStore
from .fetch import PubMedFetcher

if TYPE_CHECKING:
    from .chunk import ArticleChunker as ArticleChunkerType

ArticleChunker: type[ArticleChunkerType] | None = None
with suppress(ImportError):
    from .chunk import ArticleChunker  # type: ignore[no-redef]

__all__ = ["ArticleChunker", "ChromaDocumentStore", "PubMedFetcher"]
