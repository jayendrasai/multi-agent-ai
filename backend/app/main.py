import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import router as api_router
from app.api.auth import router as auth_router
from app.api.websocket import router as ws_router

settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate config, init DB, restore checkpoints
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown logic
    logger.info("Shutting down")


app = FastAPI(
    title="AI Orchestrator API",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix=settings.api_v1_str)
app.include_router(auth_router, prefix=settings.api_v1_str)
app.include_router(ws_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app_name": settings.app_name}
