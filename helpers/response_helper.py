"""Response construction helpers for MediMind AI."""

from __future__ import annotations

from typing import Any

from config.constants import DEFAULT_ERROR_MESSAGE, DEFAULT_SUCCESS_MESSAGE
from app_logging.logger import get_logger
from schemas.response.base_response import BaseResponse
from schemas.response.error_response import ErrorResponse

logger = get_logger(__name__)


def success_response(message: str = DEFAULT_SUCCESS_MESSAGE, data: Any | None = None, request_id: str = "") -> dict[str, Any]:
    """Build a standardized success payload."""
    logger.debug("Success response constructed", response_message=message)
    response = BaseResponse[Any](success=True, message=message, data=data, request_id=request_id)
    return response.model_dump(exclude_none=False)


def error_response(
    message: str = DEFAULT_ERROR_MESSAGE,
    data: Any | None = None,
    request_id: str = "",
    error_code: str | None = None,
    status_code: int | None = None,
) -> dict[str, Any]:
    """Build a standardized error payload."""
    logger.debug("Error response constructed", response_message=message, error_code=error_code)
    response = ErrorResponse(
        success=False,
        message=message,
        data=data,
        request_id=request_id,
        error_code=error_code,
        status_code=status_code,
    )
    return response.model_dump(exclude_none=False)
