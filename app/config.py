from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    database_sync_url: str

    # Redis
    redis_url: str

    # SearXNG
    searxng_url: str
    searxng_base_url: Optional[str] = None

    # OpenRouter
    openrouter_api_key: str
    openrouter_text_model: str
    openrouter_image_model: str

    # Google APIs (optional — Fact Check Tools, Rich Results Test)
    google_api_key: Optional[str] = None

    # LangGraph
    langgraph_checkpoint_type: str

    # Storage
    storage_images_path: str    
    storage_pdfs_path: str

    # Logging
    log_level: str

    # Application
    app_host: str
    app_port: int

    # Feature Flags
    enable_image_generation: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
