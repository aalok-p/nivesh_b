from functools import lru_cache
from typing import List
import os

class Settings:
    app_name: str ="Nivesh.ai"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: list[str] = [
        item.strip()
        for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if item.strip()
    ]
    blostem_api_base: str = os.getenv("BLOSTEM_API_BASE", "https://blostem.com/api/v1")
    blostem_api_key: str | None = os.getenv("BLOSTEM_API_KEY")
@lru_cache
def get_settings() -> Settings:
    return Settings()