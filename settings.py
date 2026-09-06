from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env"""

    # LLM Configuration
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4-turbo"

    # LangChain Configuration
    langchain_api_key: Optional[str] = None
    langchain_tracing_v2: bool = False

    # Brave Search Configuration
    brave_search_api_key: Optional[str] = None

    # Application
    log_level: str = "INFO"
    app_name: str = "langgraph-learn"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
