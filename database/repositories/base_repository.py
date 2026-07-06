"""Generic CRUD repository base class for SQLAlchemy models."""

from __future__ import annotations

import time
from typing import Any, Callable, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.base import Base
from exceptions.custom_exceptions import DatabaseException

ModelType = TypeVar("ModelType", bound=Base)

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType]):
    """Provide reusable CRUD operations for future model-specific repositories."""

    def __init__(self, model: type[ModelType], session: Session, request_id: str = "") -> None:
        self._model = model
        self._session = session
        self._request_id = request_id

    def create(self, instance: ModelType) -> ModelType:
        """Persist a new model instance."""
        return self._execute("create", lambda: self._create(instance), instance=instance)

    def add(self, instance: ModelType) -> ModelType:
        """Add and flush a model instance inside an active transaction without committing."""
        return self._execute("add", lambda: self._add(instance), instance=instance)

    def get_by_id(self, record_id: Any) -> ModelType | None:
        """Fetch a single row by primary key."""
        return self._execute("get_by_id", lambda: self._session.get(self._model, record_id))

    def get_all(self) -> list[ModelType]:
        """Return every row for the model."""
        return self._execute("get_all", lambda: list(self._session.scalars(select(self._model)).all()))

    def list_by_patient_id(self, patient_id: Any) -> list[ModelType]:
        """Fetch all rows matching a specific patient_id."""
        return self._execute(
            "list_by_patient_id",
            lambda: list(self._session.scalars(select(self._model).filter_by(patient_id=patient_id)).all()),
            patient_id=patient_id,
        )

    def update(self, instance: ModelType) -> ModelType:
        """Persist changes on an existing row."""
        return self._execute("update", lambda: self._update(instance), instance=instance)

    def update_in_tx(self, instance: ModelType) -> ModelType:
        """Update and flush a model instance inside an active transaction without committing."""
        return self._execute("update_in_tx", lambda: self._update_in_tx(instance), instance=instance)

    def delete(self, instance: ModelType) -> None:
        """Hard-delete a row from the database."""
        self._execute("delete", lambda: self._delete(instance), instance=instance)

    def delete_in_tx(self, instance: ModelType) -> None:
        """Delete and flush a model instance inside an active transaction without committing."""
        self._execute("delete_in_tx", lambda: self._delete_in_tx(instance), instance=instance)

    def exists(self, **filters: Any) -> bool:
        """Check whether at least one row matches the provided filters."""
        return self._execute("exists", lambda: self._exists(**filters))

    def count(self, **filters: Any) -> int:
        """Count rows that match the provided filters."""
        return self._execute("count", lambda: self._count(**filters))

    def _create(self, instance: ModelType) -> ModelType:
        self._session.add(instance)
        self._session.flush()
        self._session.refresh(instance)
        self._session.commit()
        return instance

    def _add(self, instance: ModelType) -> ModelType:
        self._session.add(instance)
        self._session.flush()
        self._session.refresh(instance)
        return instance

    def _update(self, instance: ModelType) -> ModelType:
        self._session.add(instance)
        self._session.flush()
        self._session.refresh(instance)
        self._session.commit()
        return instance

    def _update_in_tx(self, instance: ModelType) -> ModelType:
        self._session.add(instance)
        self._session.flush()
        self._session.refresh(instance)
        return instance

    def _delete(self, instance: ModelType) -> None:
        self._session.delete(instance)
        self._session.commit()

    def _delete_in_tx(self, instance: ModelType) -> None:
        self._session.delete(instance)
        self._session.flush()

    def _exists(self, **filters: Any) -> bool:
        statement = select(self._model).filter_by(**filters).limit(1)
        return self._session.scalars(statement).first() is not None

    def _count(self, **filters: Any) -> int:
        statement = select(func.count()).select_from(self._model).filter_by(**filters)
        return int(self._session.scalar(statement) or 0)

    def _execute(
        self,
        operation: str,
        callback: Callable[[], Any],
        instance: ModelType | None = None,
        patient_id: Any = None,
    ) -> Any:
        start_time = time.perf_counter()
        pid = patient_id if patient_id is not None else getattr(instance, "patient_id", None)
        log_fields = {
            "operation": operation,
            "table_name": self._model.__tablename__,
            "model": self._model.__name__,
            "request_id": self._request_id,
        }
        if pid is not None:
            log_fields["patient_id"] = str(pid)

        try:
            result = callback()
            logger.info(
                "Repository operation completed",
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
                **log_fields,
            )
            return result
        except Exception as exc:
            self._session.rollback()
            logger.error(
                "Repository operation failed",
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
                error=str(exc),
                **log_fields,
            )
            if isinstance(exc, DatabaseException):
                raise
            raise DatabaseException(message=str(exc)) from exc
