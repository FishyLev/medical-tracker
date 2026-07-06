from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Medical AI Assistant"
    app_version: str = "0.1.0"
    debug: bool = True
    api_prefix: str = "/api"

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_timeout_ms: int = 30000

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    app_url: str = "http://localhost:5173"
    app_title: str = "Medical AI Assistant"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_ms: int = 30000

    sqlite_db_path: str = "app.db"
    chroma_persist_dir: str = "chroma_db"
    chroma_collection_name: str = "medical_assistant_memory"
    documents_dir: str = "documents"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()