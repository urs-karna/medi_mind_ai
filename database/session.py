"""Database session helpers for MediMind AI."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app_logging.logger import get_logger
from database.connection import get_engine

logger = get_logger(__name__)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it always closes cleanly.

    Use as a FastAPI dependency::

        @router.post("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session commits on success, rolls back on error, and always closes.
    """
    db = SessionLocal(bind=get_engine())
    try:
        yield db
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Database session operation failed", error=str(exc))
        raise
    finally:
        db.close()