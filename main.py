from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

settings= get_settings()
app = FastAPI(title="Nivesh", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.get("/health", response_model="str")
async def health() ->str:
    return str(status="ok")
