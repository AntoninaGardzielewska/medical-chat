import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.retrieve import retrieve
from rag.synthesize import synthesize
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class Reference(BaseModel):
    number: int
    pmid: str
    title: str
    authors: str
    journal: str
    year: str
    pubmed_url: str


class ChatResponse(BaseModel):
    disclaimer: str
    answer: str
    references: list[Reference]
    include_sources: bool


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    start_total = time.perf_counter()
    logger.info("chat request started")

    start_retrieve = time.perf_counter()
    chunks = retrieve(
        request.question,
        max_results=settings.retrieval_max_results,
        max_distance=settings.retrieval_max_distance,
    )
    retrieve_time = time.perf_counter() - start_retrieve
    logger.info(
        "retrieve completed in %.3f s (chunks=%d)",
        retrieve_time,
        len(chunks),
    )

    start_synthesize = time.perf_counter()
    result = synthesize(request.question, chunks)
    synthesize_time = time.perf_counter() - start_synthesize
    total_time = time.perf_counter() - start_total
    logger.info(
        "synthesize completed in %.3f s; total chat time %.3f s",
        synthesize_time,
        total_time,
    )

    return ChatResponse(**result)
