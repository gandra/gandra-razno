"""FastAPI application entry point with plugin autodiscovery."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gandra_tools.core.config import get_settings
from gandra_tools.core.errors import register_error_handlers
from gandra_tools.core.logging import setup_logging
from gandra_tools.core.plugin import registry
from gandra_tools.db.session import close_db, init_db
from gandra_tools.routers import auth, health, publish

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Gandra Tools API...")
    await init_db()
    registry.discover()
    logger.info("Discovered %d tool plugin(s): %s", len(registry.tools), list(registry.tools.keys()))
    yield
    logger.info("Shutting down...")
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Gandra Tools API",
        description="Swiss-army toolset — YouTube transcripts, RAG research, file ops, and more",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Error handlers
    register_error_handlers(app)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(publish.router)

    # Tool routers (from plugin autodiscovery)
    for tool_router in registry.routers:
        app.include_router(tool_router)

    return app


app = create_app()
