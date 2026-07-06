"""Authentication dependencies for protected routes."""

from __future__ import annotations

from typing import Any

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app_logging.logger import get_logger
from core.auth.auth_service import AuthService
from exceptions.custom_exceptions import AuthenticationException
from middleware.token_context import assign_token_context

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict[str, Any]:
    """Resolve the authenticated user from the Authorization header.

    After validation the ``user_id`` and ``patient_id`` are stored on
    ``request.state`` via :func:`assign_token_context` so they are
    available to all downstream code for this request.
    """
    request_id = getattr(request.state, "request_id", "")
    if credentials is None or not credentials.credentials:
        logger.warning("Authorization header missing", request_id=request_id)
        raise AuthenticationException("Authorization token is required")

    service = AuthService()
    user_data = service.get_current_user(credentials.credentials, request_id=request_id)

    # Store user_id and patient_id on the request for downstream use
    assign_token_context(
        request,
        user_id=user_data.get("user_id"),
        patient_id=(user_data.get("patient") or {}).get("patient_id"),
    )

    return user_data