"""LangGraph state schema for conversational healthcare chat routing."""

from __future__ import annotations

from typing import Any, TypedDict


class ChatGraphState(TypedDict, total=False):
    """Represents the shared state passed between nodes in the chat routing graph."""

    patient_id: str
    session_id: str | None
    question: str
    conversation_history: list[dict[str, Any]]
    intent: str
    structured_results: list[dict[str, Any]]
    retrieved_chunks: list[Any]
    answer: str
    citations: list[dict[str, Any]]
