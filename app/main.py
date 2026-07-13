from contextlib import asynccontextmanager
from time import perf_counter
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, documents, memory, users
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import InMemoryRateLimiter
from app.db.database import init_db
from app.services.local_llm import load_local_model

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()
init_db()

chat_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)
doc_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
model_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_loaded
    load_local_model()
    model_loaded = True
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.94.32:5173",
    "https://medical-assistant-v3.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    logger.info(
        "request_completed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown",
        },
    )
    return response


@app.middleware("http")
async def limiter_middleware(request: Request, call_next):
    if request.url.path.endswith("/api/chat"):
        chat_limiter.check(request)
    if request.url.path.endswith("/api/documents"):
        doc_limiter.check(request)
    return await call_next(request)


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
        "model_loaded": model_loaded,
        "db_ready": True,
        "worker_pid": os.getpid(),
        "llm_provider": getattr(settings, "llm_provider", "unknown"),
        "llm_model": getattr(settings, "llm_model", "unknown"),
    }


app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)