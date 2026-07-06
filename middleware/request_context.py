"""Middleware for request tracking and execution timing."""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.constants import REQUEST_ID_HEADER
from app_logging.logger import clear_log_context, get_logger, set_log_context

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request metadata and measure execution time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process an incoming request with a request-scoped context."""
        request_id = str(uuid4())
        start_time = time.perf_counter()
        request.state.request_id = request_id
        request.state.user_id = None
        set_log_context(request_id=request_id, user_id=None)

        response: Response | None = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Request processed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                execution_time_ms=execution_time_ms,
            )
            clear_log_context()
