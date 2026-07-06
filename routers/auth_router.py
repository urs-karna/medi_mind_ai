"""Authentication router for MediMind AI."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.auth.dependencies import get_current_user
from handlers.auth_handler import AuthHandler
from schemas.request.auth_request import LoginRequest, RegisterRequest
from schemas.response.auth_response import LogoutResponse, TokenResponse, UserResponse

router = APIRouter(tags=["Auth"])
auth_handler = AuthHandler()


@router.post("/register", response_model=UserResponse)
async def register(request: Request, request_data: RegisterRequest) -> UserResponse:
    """Create a user and linked patient profile."""
    request_id = getattr(request.state, "request_id", "")
    return auth_handler.register(request_data=request_data, request_id=request_id)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, request_data: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT."""
    request_id = getattr(request.state, "request_id", "")
    return auth_handler.login(request_data=request_data, request_id=request_id)


@router.get("/me", response_model=UserResponse)
async def me(request: Request, current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user and linked patient profile."""
    request_id = getattr(request.state, "request_id", "")
    return auth_handler.me(current_user=current_user, request_id=request_id)


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request) -> LogoutResponse:
    """Confirm logout for stateless JWT clients."""
    request_id = getattr(request.state, "request_id", "")
    return auth_handler.logout(request_id=request_id)