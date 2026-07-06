"""API router for RAG retrieval search debug and testing endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from exceptions.custom_exceptions import AuthenticationException
from handlers.retrieval_handler import RetrievalHandler
from schemas.request.retrieval_request import RetrievalSearchRequest
from schemas.retrieval.retrieval_schemas import RetrievalResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/retrieval", tags=["Retrieval"])
retrieval_handler = RetrievalHandler()


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.post("/search", response_model=RetrievalResponse)
async def search_retrieval(
    request: Request,
    body: RetrievalSearchRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> RetrievalResponse:
    """Debug/testing endpoint for semantic vector retrieval over patient medical chunks."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return retrieval_handler.search(
        question=body.question,
        patient_id=patient_id,
        top_k=body.top_k or 5,
        request_id=request_id,
    )
