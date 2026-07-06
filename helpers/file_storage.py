"""File storage utility helpers for uploading medical documents."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from app_logging.logger import get_logger
from config.constants import ALLOWED_DOCUMENT_TYPES, DOCUMENT_STORAGE_BASE_PATH, MAX_DOCUMENT_SIZE_MB
from exceptions.custom_exceptions import DocumentProcessingException, ValidationException

logger = get_logger(__name__)


def save_uploaded_file(patient_id: UUID | str, file: UploadFile) -> str:
    """Validate and persist an uploaded medical document to storage.

    Returns the relative storage URI path as a plain string.
    """
    original_filename = file.filename or "untitled_document"
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_DOCUMENT_TYPES:
        logger.warning(
            "Document upload rejected: unsupported file type",
            patient_id=str(patient_id),
            filename=original_filename,
            extension=extension,
        )
        raise ValidationException(
            f"Unsupported file extension '{extension}'. Allowed types: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
        )

    # Validate file size before writing to disk
    max_bytes = MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    try:
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception as exc:
        logger.error("Failed to inspect uploaded file size", error=str(exc))
        raise DocumentProcessingException("Could not inspect uploaded file size") from exc

    if file_size > max_bytes:
        logger.warning(
            "Document upload rejected: file size exceeds limit",
            patient_id=str(patient_id),
            filename=original_filename,
            file_size_bytes=file_size,
            max_bytes=max_bytes,
        )
        raise ValidationException(
            f"File size ({round(file_size / (1024 * 1024), 2)} MB) exceeds the maximum allowed size of {MAX_DOCUMENT_SIZE_MB} MB"
        )

    unique_id = uuid4()
    safe_filename = f"{unique_id}_{original_filename}"
    storage_dir = Path(DOCUMENT_STORAGE_BASE_PATH) / str(patient_id)
    target_path = storage_dir / safe_filename
    relative_uri = f"{DOCUMENT_STORAGE_BASE_PATH}/{patient_id}/{safe_filename}"

    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        with target_path.open("wb") as buffer:
            while chunk := file.file.read(1024 * 64):
                buffer.write(chunk)
        logger.info(
            "File successfully saved to storage",
            patient_id=str(patient_id),
            relative_uri=relative_uri,
            file_size_bytes=file_size,
        )
        return relative_uri
    except Exception as exc:
        logger.error(
            "Failed to save file to disk",
            patient_id=str(patient_id),
            target_path=str(target_path),
            error=str(exc),
        )
        # Cleanup partially written file if failure occurred during write
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass
        raise DocumentProcessingException("Failed to save uploaded document to storage") from exc


def read_file(uri: str) -> bytes:
    """Read binary file contents from local storage URI."""
    file_path = Path(uri)
    if not file_path.exists():
        logger.error("Storage file not found", uri=uri)
        raise DocumentProcessingException(f"Stored file '{uri}' not found on disk")
    try:
        return file_path.read_bytes()
    except Exception as exc:
        logger.error("Failed to read storage file bytes", uri=uri, error=str(exc))
        raise DocumentProcessingException(f"Could not read file '{uri}'") from exc


def get_mime_type(uri: str) -> str:
    """Map file extension to standard MIME type string."""
    extension = Path(uri).suffix.lower()
    if extension == ".pdf":
        return "application/pdf"
    if extension == ".png":
        return "image/png"
    if extension in (".jpg", ".jpeg"):
        return "image/jpeg"
    return "application/octet-stream"
