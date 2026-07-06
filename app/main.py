"""FastAPI application entry point for MediMind AI."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.constants import API_PREFIX, APP_DESCRIPTION, APP_TITLE, APP_VERSION
from config.settings import get_settings
from database.base import Base
from database.connection import connect_with_retry, get_engine, monitor_connection
from exceptions.exception_handler import register_exception_handlers
import models
from app_logging.logger import get_logger
from middleware.request_context import RequestContextMiddleware
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.database_router import router as database_router
from routers.document_router import router as document_router
from routers.health_router import router as health_router
from routers.patient_profile_router import router as patient_profile_router
from routers.retrieval_router import router as retrieval_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage startup and shutdown lifecycle events.

    On startup:
      1. Connect to the database with retry logic.
      2. Launch a background monitor that pings the DB periodically.

    On shutdown:
      1. Cancel the monitor task.
      2. Dispose of the database engine.
    """
    # ── Startup ──────────────────────────────────────────────
    connected = connect_with_retry()
    if connected:
        logger.info("Database ready — starting connection monitor")
        try:
            Base.metadata.create_all(bind=get_engine())
            logger.info("Database tables verified/created via ORM")
        except Exception as exc:
            logger.error("Failed to create database tables via ORM", error=str(exc))
    else:
        logger.critical("Application starting WITHOUT database connectivity")

    try:
        from agents.pinecone_client import ensure_index_exists
        ensure_index_exists()
        logger.info("Pinecone vector index verified at startup")
    except Exception as exc:
        logger.error("Failed to verify/create Pinecone vector index at startup", error=str(exc))

    monitor_task = asyncio.create_task(monitor_connection())

    yield  # ← application runs while yielded

    # ── Shutdown ─────────────────────────────────────────────
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    try:
        get_engine().dispose()
        logger.info("Database engine disposed on shutdown")
    except Exception:
        pass
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name or APP_TITLE,
        version=settings.app_version or APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    register_exception_handlers(application)
    application.include_router(auth_router, prefix=API_PREFIX)
    application.include_router(chat_router, prefix=API_PREFIX)
    application.include_router(database_router, prefix=API_PREFIX)
    application.include_router(document_router, prefix=API_PREFIX)
    application.include_router(health_router, prefix=API_PREFIX)
    application.include_router(patient_profile_router, prefix=API_PREFIX)
    application.include_router(retrieval_router, prefix=API_PREFIX)
    logger.info("FastAPI application initialized")
    return application


app = create_app()
