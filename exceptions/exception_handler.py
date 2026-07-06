"""Centralized exception handlers for MediMind AI."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config.constants import DEFAULT_ERROR_MESSAGE, DEFAULT_VALIDATION_ERROR_MESSAGE
from exceptions.custom_exceptions import BaseAppException
from helpers.response_helper import error_response
from app_logging.logger import get_logger

logger = get_logger(__name__)


async def handle_app_exception(request: Request, exc: BaseAppException) -> JSONResponse:
    """Convert application exceptions into standardized JSON responses."""
    request_id = getattr(request.state, "request_id", "")
    logger.error(
        "Application exception handled",
        error_code=exc.error_code,
        status_code=exc.status_code,
    )
    payload = error_response(
        message=exc.message,
        data=exc.details,
        request_id=request_id,
        error_code=exc.error_code,
        status_code=exc.status_code,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Convert validation errors into standardized JSON responses."""
    request_id = getattr(request.state, "request_id", "")
    logger.warning("Request validation failed")
    payload = error_response(
        message=DEFAULT_VALIDATION_ERROR_MESSAGE,
        data={"errors": exc.errors()},
        request_id=request_id,
        error_code="VALIDATION_ERROR",
        status_code=422,
    )
    return JSONResponse(status_code=422, content=payload)


async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Convert unexpected errors into a safe generic response."""
    request_id = getattr(request.state, "request_id", "")
    logger.critical("Unhandled application exception", exception_type=type(exc).__name__)
    payload = error_response(
        message=DEFAULT_ERROR_MESSAGE,
        request_id=request_id,
        error_code="INTERNAL_SERVER_ERROR",
        status_code=500,
    )
    return JSONResponse(status_code=500, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all centralized handlers on the FastAPI application."""
    handlers: list[tuple[type[Exception], Callable[..., object]]] = [
        (BaseAppException, handle_app_exception),
        (RequestValidationError, handle_validation_exception),
        (Exception, handle_unhandled_exception),
    ]
    for exception_type, handler in handlers:
        app.add_exception_handler(exception_type, handler)
