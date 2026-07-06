"""Structured JSON logging utilities for MediMind AI."""

from __future__ import annotations

import inspect
import json
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from config.constants import LOG_DIRECTORY, LOG_FILE_NAME, LOG_LEVELS

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_context: ContextVar[str | None] = ContextVar("user_id", default=None)

_log_lock = Lock()


@dataclass(frozen=True, slots=True)
class LogContext:
    """Request-scoped logging context."""

    request_id: str | None = None
    user_id: str | None = None


def set_log_context(request_id: str | None = None, user_id: str | None = None) -> None:
    """Set request-scoped log context values."""
    if request_id is not None:
        request_id_context.set(request_id)
    if user_id is not None:
        user_id_context.set(user_id)


def clear_log_context() -> None:
    """Clear request-scoped log context values."""
    request_id_context.set(None)
    user_id_context.set(None)


def get_log_context() -> LogContext:
    """Return the current request-scoped log context."""
    return LogContext(
        request_id=request_id_context.get(),
        user_id=user_id_context.get(),
    )


def _ensure_log_file() -> Path:
    """Create the log directory and file if they do not already exist."""
    log_directory = Path(LOG_DIRECTORY)
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / LOG_FILE_NAME
    log_file.touch(exist_ok=True)
    return log_file


class StructuredLogger:
    """Minimal JSON logger that emits normalized structured logs to disk."""

    def __init__(self, module_name: str) -> None:
        self._module_name = module_name
        self._log_file = _ensure_log_file()

    def debug(self, message: str, **fields: Any) -> None:
        """Emit a debug log entry."""
        self._log("DEBUG", message, fields)

    def info(self, message: str, **fields: Any) -> None:
        """Emit an informational log entry."""
        self._log("INFO", message, fields)

    def warning(self, message: str, **fields: Any) -> None:
        """Emit a warning log entry."""
        self._log("WARNING", message, fields)

    def error(self, message: str, **fields: Any) -> None:
        """Emit an error log entry."""
        self._log("ERROR", message, fields)

    def critical(self, message: str, **fields: Any) -> None:
        """Emit a critical log entry."""
        self._log("CRITICAL", message, fields)

    def _log(self, level: str, message: str, fields: dict[str, Any]) -> None:
        """Render a structured JSON log line to the project log file."""
        if level not in LOG_LEVELS:
            level = "INFO"

        context = get_log_context()
        function_name = fields.pop("function_name", None)
        if function_name is None:
            function_name = inspect.stack()[2].function

        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "request_id": context.request_id,
            "user_id": context.user_id,
            "module_name": self._module_name,
            "function_name": function_name,
            "message": message,
        }
        payload.update(fields)

        with _log_lock:
            with self._log_file.open("a", encoding="utf-8") as log_stream:
                log_stream.write(json.dumps(payload, default=str, ensure_ascii=True) + "\n")


def get_logger(module_name: str | None = None) -> StructuredLogger:
    """Return a structured logger for the requested module."""
    return StructuredLogger(module_name or __name__)
