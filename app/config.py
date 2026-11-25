from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="allow")
    
    # Database
    database_url: str
    database_sync_url: str

    # Redis
    redis_url: str

    # SearXNG
    searxng_url: str

    # OpenRouter
    openrouter_api_key: str
    openrouter_text_model: str

    # Google APIs (optional — Fact Check Tools)
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
    enable_backlinks: bool = True

    # WordPress Encryption
    encryption_key: Optional[str] = None

    # Custom SQL connector
    # Public base URL of this API used to build absolute image URLs for
    # remote websites (e.g. https://api.example.com). Optional.
    public_api_url: Optional[str] = None
    # Allow connector URLs pointing at private/loopback addresses (dev only)
    sql_connector_allow_private: bool = True


settings = Settings()
