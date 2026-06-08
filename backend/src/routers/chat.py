from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.rag.retrieve import retrieve
from backend.rag.rewrite import rewrite_query
from backend.rag.synthesize import synthesize

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


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    rewritten = rewrite_query(request.question)
    chunks = retrieve(rewritten, k=5)
    result = synthesize(request.question, chunks)

    return ChatResponse(**result)
