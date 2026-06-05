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
    cors_origins: list[str] = ["http://localhost:3000"]

    # Anthropic
    anthropic_api_key: str = ""

    # Database (future use)
    database_url: str = ""

    # ChromaDB (future use)
    chroma_db_path: str = "./chroma_db"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()
