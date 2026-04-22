from functools import lru_cache
from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str ="Nivesh.ai"
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: list[str] = [
        item.strip().rstrip("/")
        for item in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,https://niveshsathi-nine.vercel.app",
        ).split(",")
        if item.strip()
    ]
    blostem_api_base: str = os.getenv("BLOSTEM_API_BASE", "https://blostem.com/api/v1")
    blostem_api_key: str | None = os.getenv("BLOSTEM_API_KEY")
@lru_cache
def get_settings() -> Settings:
    return Settings()
