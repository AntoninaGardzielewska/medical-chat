"""Chat router - placeholder implementation."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: str | None = None


class ChatResponse(BaseModel):
    message: ChatMessage
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return a response.

    Placeholder: returns a static response until LLM integration is wired up.
    """
    return ChatResponse(
        message=ChatMessage(
            role="assistant",
            content=(
                "Hello! I'm your medical assistant. "
                "This is a placeholder response — full AI integration coming soon."
            ),
        ),
        session_id=request.session_id or "placeholder-session",
    )
