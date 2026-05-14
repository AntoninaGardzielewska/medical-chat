"""Medical Chat Backend - FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import chat, health

app = FastAPI(
    title="Medical Chat API",
    description="AI-powered medical chat backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
