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
    searxng_base_url: Optional[str] = None

    # OpenRouter
    openrouter_api_key: str
    openrouter_text_model: str

    # Hugging Face (for image generation)
    hf_token: Optional[str] = None
    qwen_space_id: Optional[str] = None
    hf_fallback_model: Optional[str] = None
    image_backend: Optional[str] = None

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
    enable_backlinks: bool = True

    # WordPress Encryption
    encryption_key: Optional[str] = None


settings = Settings()
