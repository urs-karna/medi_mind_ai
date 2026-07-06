"""API router for document upload, retrieval, and listing endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app_logging.logger import get_logger
from core.auth.dependencies import get_current_user
from exceptions.custom_exceptions import AuthenticationException
from handlers.document_handler import DocumentHandler
from schemas.response.base_response import BaseResponse
from schemas.response.document_response import DocumentListResponse, DocumentResponse, ExtractionStatusResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])
document_handler = DocumentHandler()


def _extract_patient_id(request: Request, current_user: dict[str, Any]) -> str:
    """Safely resolve the patient_id from request token context or current user profile."""
    patient_id = getattr(request.state, "patient_id", None)
    if not patient_id:
        patient = current_user.get("patient") or {}
        patient_id = patient.get("patient_id")
    if not patient_id:
        raise AuthenticationException("Authenticated user does not have a linked patient profile")
    return str(patient_id)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
    """Upload a medical document image or PDF for background processing."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return document_handler.upload_document(
        patient_id=patient_id,
        file=file,
        document_type=document_type,
        request_id=request_id,
    )


@router.post("/{document_id}/process", response_model=ExtractionStatusResponse)
async def process_document(
    request: Request,
    document_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ExtractionStatusResponse:
    """Trigger synchronous AI vision OCR, structured extraction, and clinical table persistence for an uploaded document."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return document_handler.process_document(
        patient_id=patient_id,
        document_id=document_id,
        request_id=request_id,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    request: Request,
    document_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
    """Retrieve metadata and status for a single document owned by the requesting patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return document_handler.get_document(
        patient_id=patient_id,
        document_id=document_id,
        request_id=request_id,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> DocumentListResponse:
    """Retrieve a paginated list of documents uploaded by the requesting patient."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return document_handler.list_documents(
        patient_id=patient_id,
        limit=limit,
        offset=offset,
        request_id=request_id,
    )


@router.delete("/{document_id}", response_model=BaseResponse[Any])
async def delete_document(
    request: Request,
    document_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> BaseResponse[Any]:
    """Soft-delete a document and cascade delete its derived database records and vector index chunks."""
    request_id = getattr(request.state, "request_id", "")
    patient_id = _extract_patient_id(request, current_user)
    return document_handler.delete_document(
        patient_id=patient_id,
        document_id=document_id,
        request_id=request_id,
    )
