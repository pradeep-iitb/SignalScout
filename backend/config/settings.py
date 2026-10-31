import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-3.8-flash"
    GEMINI_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    XAI_MODEL: str = "grok-3-mini"
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    CRUSTDATA_API_KEY: Optional[str] = None
    CRUSTDATA_API_VERSION: str = "2025-11-01"
    CRUSTDATA_BASE_URL: str = "https://api.crustdata.com"
    
    WEB_SEARCH_API_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        extra = "ignore"

settings = Settings()
