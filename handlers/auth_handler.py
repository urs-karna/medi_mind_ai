"""Authentication orchestration handler."""

from __future__ import annotations

from typing import Any

from app_logging.logger import get_logger
from config.constants import DEFAULT_SUCCESS_MESSAGE
from core.auth.auth_service import AuthService
from helpers.response_helper import success_response
from schemas.request.auth_request import LoginRequest, RegisterRequest
from schemas.response.auth_response import LogoutResponse, TokenResponse, UserResponse

logger = get_logger(__name__)


class AuthHandler:
    """Convert auth service results into API response models."""

    def __init__(self, service: AuthService | None = None) -> None:
        self._service = service or AuthService()

    def register(self, request_data: RegisterRequest, request_id: str = "") -> UserResponse:
        """Handle the registration flow."""
        logger.info("Auth register requested", request_id=request_id)
        data = self._service.register_user(request_data, request_id=request_id)
        payload = success_response(message=DEFAULT_SUCCESS_MESSAGE, data=data, request_id=request_id)
        return UserResponse.model_validate(payload)

    def login(self, request_data: LoginRequest, request_id: str = "") -> TokenResponse:
        """Handle the login flow."""
        logger.info("Auth login requested", request_id=request_id)
        data = self._service.authenticate_user(request_data, request_id=request_id)
        payload = success_response(message=DEFAULT_SUCCESS_MESSAGE, data=data, request_id=request_id)
        return TokenResponse.model_validate(payload)

    def me(self, current_user: dict[str, Any], request_id: str = "") -> UserResponse:
        """Wrap the resolved current user into the standard response envelope."""
        logger.info("Current user requested", request_id=request_id)
        payload = success_response(message=DEFAULT_SUCCESS_MESSAGE, data=current_user, request_id=request_id)
        return UserResponse.model_validate(payload)

    def logout(self, request_id: str = "") -> LogoutResponse:
        """Return a stateless logout confirmation."""
        logger.info("Auth logout requested", request_id=request_id)
        data = self._service.logout_user(request_id=request_id)
        payload = success_response(message=DEFAULT_SUCCESS_MESSAGE, data=data, request_id=request_id)
        return LogoutResponse.model_validate(payload)