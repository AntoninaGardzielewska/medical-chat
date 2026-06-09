"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Anthropic
    anthropic_api_key: str = ""

    # Database (future use)
    database_url: str = ""

    # ChromaDB (future use)
    chroma_db_path: str = "./chroma_db"

    # Embeddings
    embedding_model_name: str = "neuml/pubmedbert-base-embeddings"

    # Retrieval tuning
    retrieval_max_results: int = 20
    retrieval_max_distance: float = 0.35

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_name: str = "llama3.2:latest"


settings = Settings()
