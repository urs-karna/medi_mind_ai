"""LangChain client wrapper for generating grounded healthcare chat responses using Gemini."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app_logging.logger import get_logger
from config.constants import CHAT_MODEL, MessageRole
from config.settings import get_settings
from exceptions.custom_exceptions import ChatGenerationException

logger = get_logger(__name__)


def generate_chat_response(
    system_prompt: str,
    conversation_history: list[dict[str, Any]],
    context_chunks: list[str],
    question: str,
    request_id: str = "",
) -> str:
    """Invoke Gemini with system safety prompt, history, retrieved medical chunks, and patient question."""
    settings = get_settings()
    if not settings.google_api_key:
        raise ChatGenerationException("GOOGLE_API_KEY is not configured in settings")

    messages: list[Any] = [SystemMessage(content=system_prompt)]

    for turn in conversation_history:
        role = turn.get("role")
        content = str(turn.get("content", ""))
        if role in ("user", MessageRole.USER, MessageRole.USER.value):
            messages.append(HumanMessage(content=content))
        elif role in ("assistant", MessageRole.ASSISTANT, MessageRole.ASSISTANT.value):
            messages.append(AIMessage(content=content))

    chunks_formatted = (
        "\n\n".join(f"--- Record Chunk ---\n{c}" for c in context_chunks)
        if context_chunks
        else "No relevant medical records found."
    )
    final_content = f"Relevant medical records:\n{chunks_formatted}\n\nPatient question: {question}"
    messages.append(HumanMessage(content=final_content))

    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model=CHAT_MODEL,
            google_api_key=settings.google_api_key,
            temperature=0.2,
        )
        response = llm.invoke(messages)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Chat LLM response generation completed",
            model=CHAT_MODEL,
            latency_ms=latency_ms,
            request_id=request_id,
        )
        return str(response.content)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Chat LLM response generation failed",
            model=CHAT_MODEL,
            latency_ms=latency_ms,
            error=str(exc),
            request_id=request_id,
        )
        if isinstance(exc, ChatGenerationException):
            raise
        raise ChatGenerationException(f"Chat generation failed: {exc}") from exc
