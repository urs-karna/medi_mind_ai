"""Keyword-based router node for directing chat questions to History or RAG flows."""

from __future__ import annotations

from agents.graph_state import ChatGraphState
from app_logging.logger import get_logger
from config.constants import (
    EXPLANATION_OVERRIDE_KEYWORDS,
    LAB_HISTORY_KEYWORDS,
    LISTING_TRIGGER_WORDS,
    PRESCRIPTION_HISTORY_KEYWORDS,
)

logger = get_logger(__name__)


def classify_intent(state: ChatGraphState) -> ChatGraphState:
    """Classify user question intent using keyword substring matching without LLM invocation."""
    question_lower = state.get("question", "").lower()

    override_kw = next((kw for kw in EXPLANATION_OVERRIDE_KEYWORDS if kw in question_lower), None)
    if override_kw:
        intent = "medical_qa"
        rule_fired = "explanation_override"
        matched_keyword = override_kw
    else:
        trigger_kw = next((kw for kw in LISTING_TRIGGER_WORDS if kw in question_lower), None)
        entity_kw = next(
            (kw for kw in LAB_HISTORY_KEYWORDS + PRESCRIPTION_HISTORY_KEYWORDS if kw in question_lower),
            None,
        )
        if trigger_kw and entity_kw:
            intent = "history_query"
            rule_fired = "listing_match"
            matched_keyword = f"{trigger_kw} + {entity_kw}"
        else:
            intent = "medical_qa"
            rule_fired = "default_rag"
            matched_keyword = None

    state["intent"] = intent

    logger.info(
        "Chat router intent classified",
        patient_id=state.get("patient_id", ""),
        intent=intent,
        rule_fired=rule_fired,
        matched_keyword=matched_keyword or "none",
    )

    return state
