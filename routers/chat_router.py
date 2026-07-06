"""API router for RAG medical chat assistant endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from exceptions.custom_exceptions import AuthenticationException
from helpers.response_helper import success_response
from schemas.request.chat_request import ChatMessageRequest
from schemas.response.chat_response import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatSessionListResponse,
)
from services.chat_service import ChatService

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])
chat_service = ChatService()


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.post("/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    request: Request,
    body: ChatMessageRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ChatMessageResponse:
    """Send a question to the grounded medical chat assistant."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    result = chat_service.send_message(
        patient_id=patient_id,
        session_id=body.session_id,
        question=body.question,
        request_id=request_id,
    )
    payload = success_response(data=result, request_id=request_id)
    return ChatMessageResponse.model_validate(payload)


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ChatSessionListResponse:
    """List paginated chat sessions for the authenticated patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    sessions = chat_service.list_sessions(
        patient_id=patient_id,
        limit=limit,
        offset=offset,
        request_id=request_id,
    )
    payload = success_response(data=sessions, request_id=request_id)
    return ChatSessionListResponse.model_validate(payload)


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    request: Request,
    session_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Fetch full message history for a specific chat session owned by the patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    messages = chat_service.get_session_messages(
        patient_id=patient_id,
        session_id=session_id,
        limit=limit,
        request_id=request_id,
    )
    payload = success_response(data=messages, request_id=request_id)
    return ChatHistoryResponse.model_validate(payload)
