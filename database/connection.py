"""SQLAlchemy engine configuration with retry and monitoring for MediMind AI."""

from __future__ import annotations

import asyncio
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app_logging.logger import get_logger
from config.constants import (
    DB_MONITOR_PING_INTERVAL_SECONDS,
    DB_RETRY_BASE_DELAY_SECONDS,
    DB_RETRY_MAX_ATTEMPTS,
)
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()
engine: Engine | None = None


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine, creating it on first call."""
    global engine
    if engine is None:
        _create_engine()
    return engine  # type: ignore[return-value]


def _create_engine() -> None:
    """Build the SQLAlchemy engine from application settings."""
    global engine
    database_connection_string = settings.database_connection_string
    if not database_connection_string:
        raise RuntimeError(
            "DATABASE_NAME must be configured before the database engine can start"
        )

    engine = create_engine(
        database_connection_string,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=settings.database_pool_recycle,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,
    )
    logger.info(
        "Database engine created",
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
        pool_size=settings.database_pool_size,
    )


def ping_database() -> bool:
    """Execute ``SELECT 1`` to verify the database is reachable.

    Returns ``True`` on success, ``False`` on failure.
    """
    try:
        eng = get_engine()
        with eng.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database ping failed", error=str(exc))
        return False


def connect_with_retry() -> bool:
    """Attempt to connect to the database with exponential back-off.

    Retries up to ``DB_RETRY_MAX_ATTEMPTS`` times.  The delay between attempts
    increases linearly: 5 s, 10 s, 15 s, 20 s, 25 s.

    Returns ``True`` when the connection succeeds, ``False`` after all
    attempts are exhausted.
    """
    global engine

    for attempt in range(1, DB_RETRY_MAX_ATTEMPTS + 1):
        delay = DB_RETRY_BASE_DELAY_SECONDS * attempt
        try:
            _create_engine()
            with engine.connect() as connection:  # type: ignore[union-attr]
                connection.execute(text("SELECT 1"))
            logger.info(
                "Database connected successfully",
                attempt=attempt,
                host=settings.database_host,
                database=settings.database_name,
            )
            return True
        except Exception as exc:
            logger.error(
                "Database connection attempt failed",
                attempt=attempt,
                max_attempts=DB_RETRY_MAX_ATTEMPTS,
                error=str(exc),
                retry_in_seconds=delay if attempt < DB_RETRY_MAX_ATTEMPTS else None,
            )
            engine = None  # reset so next attempt rebuilds
            if attempt < DB_RETRY_MAX_ATTEMPTS:
                time.sleep(delay)

    logger.critical(
        "All database connection attempts exhausted",
        max_attempts=DB_RETRY_MAX_ATTEMPTS,
    )
    return False


async def monitor_connection() -> None:
    """Background task that pings the database periodically.

    If the ping fails, ``connect_with_retry`` is called to re-establish
    the connection.  Runs indefinitely until the application shuts down.
    """
    logger.info(
        "Database connection monitor started",
        ping_interval_seconds=DB_MONITOR_PING_INTERVAL_SECONDS,
    )
    while True:
        await asyncio.sleep(DB_MONITOR_PING_INTERVAL_SECONDS)
        if not ping_database():
            logger.warning("Database monitor detected connection failure — reconnecting")
            connect_with_retry()
        else:
            logger.debug("Database monitor ping OK")