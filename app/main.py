from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, documents, memory, users
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.database import init_db

setup_logging()
settings = get_settings()
init_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://medical-assistant-v3.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "llm_provider": getattr(settings, "llm_provider", "unknown"),
        "llm_model": getattr(settings, "llm_model", "unknown"),
    }

@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "llm_provider": getattr(settings, "llm_provider", "unknown"),
        "llm_model": getattr(settings, "llm_model", "unknown"),
    }

app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)