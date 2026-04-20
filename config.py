from functools import lru_cache
from typing import List
import os

class Settings:
    app_name: str ="Nivesh.ai"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()