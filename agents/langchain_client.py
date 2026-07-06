"""LangChain multimodal vision client wrapper forcing Pydantic structured outputs."""

from __future__ import annotations

import base64
import time

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.extraction_prompts import get_classification_prompt, get_extraction_prompt
from app_logging.logger import get_logger
from config.constants import (
    DOCUMENT_TYPE_LAB_REPORT,
    DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN,
    DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
    GEMINI_VISION_MODEL,
)
from config.settings import get_settings
from exceptions.custom_exceptions import AIExtractionException
from schemas.extraction.extraction_schemas import (
    DocumentClassificationSchema,
    GenericExtractionSchema,
    LabReportExtractionSchema,
    PrescriptionExtractionSchema,
)

logger = get_logger(__name__)


def _build_multimodal_message(image_bytes: bytes, mime_type: str, prompt: str) -> HumanMessage:
    """Format base64 image data and prompt text into a LangChain HumanMessage."""
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_uri = f"data:{mime_type};base64,{b64_image}"
    return HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_uri}},
        ]
    )


def classify_document(
    image_bytes: bytes,
    mime_type: str,
    document_id: str = "",
    request_id: str = "",
) -> DocumentClassificationSchema:
    """Classify document category and confidence using LangChain structured output."""
    settings = get_settings()
    if not settings.google_api_key:
        raise AIExtractionException("GOOGLE_API_KEY is not configured in settings")

    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_VISION_MODEL,
            google_api_key=settings.google_api_key,
            temperature=0.0,
        )
        structured_llm = llm.with_structured_output(DocumentClassificationSchema)
        prompt_text = get_classification_prompt()
        message = _build_multimodal_message(image_bytes, mime_type, prompt_text)

        result: DocumentClassificationSchema = structured_llm.invoke([message])
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Gemini Vision classification call completed successfully",
            document_id=document_id,
            model=GEMINI_VISION_MODEL,
            latency_ms=latency_ms,
            request_id=request_id,
        )
        return result
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Gemini Vision classification call failed",
            document_id=document_id,
            model=GEMINI_VISION_MODEL,
            latency_ms=latency_ms,
            error=str(exc),
            request_id=request_id,
        )
        if isinstance(exc, AIExtractionException):
            raise
        raise AIExtractionException(f"Document classification failed: {exc}") from exc


def extract_document_data(
    image_bytes: bytes,
    mime_type: str,
    document_type: str,
    document_id: str = "",
    request_id: str = "",
) -> PrescriptionExtractionSchema | LabReportExtractionSchema | GenericExtractionSchema:
    """Extract type-safe Pydantic medical data using LangChain structured output."""
    settings = get_settings()
    if not settings.google_api_key:
        raise AIExtractionException("GOOGLE_API_KEY is not configured in settings")

    if document_type in (DOCUMENT_TYPE_PRESCRIPTION_PRINTED, DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN):
        schema = PrescriptionExtractionSchema
    elif document_type == DOCUMENT_TYPE_LAB_REPORT:
        schema = LabReportExtractionSchema
    else:
        schema = GenericExtractionSchema

    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_VISION_MODEL,
            google_api_key=settings.google_api_key,
            temperature=0.0,
        )
        structured_llm = llm.with_structured_output(schema)
        prompt_text = get_extraction_prompt(document_type)
        message = _build_multimodal_message(image_bytes, mime_type, prompt_text)

        result = structured_llm.invoke([message])
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Gemini Vision structured extraction call completed successfully",
            document_id=document_id,
            model=GEMINI_VISION_MODEL,
            latency_ms=latency_ms,
            request_id=request_id,
        )
        return result
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Gemini Vision structured extraction call failed",
            document_id=document_id,
            model=GEMINI_VISION_MODEL,
            latency_ms=latency_ms,
            error=str(exc),
            request_id=request_id,
        )
        if isinstance(exc, AIExtractionException):
            raise
        raise AIExtractionException(f"Structured extraction failed: {exc}") from exc
