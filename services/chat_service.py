"""Service layer for patient chat sessions, RAG retrieval, safety grounding, and LLM orchestration."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from agents.chat_graph import build_chat_graph
from agents.chat_llm_client import generate_chat_response
from agents.chat_prompts import build_system_prompt
from app_logging.logger import get_logger
from config.constants import (
    CHAT_MODEL,
    MAX_CHAT_HISTORY_MESSAGES,
    NO_INFO_FALLBACK_MESSAGE,
    RELEVANT_SCORE_THRESHOLD,
    MessageRole,
)
from database.connection import get_engine
from database.repositories.chat_message_repository import ChatMessageRepository
from database.repositories.chat_retrieval_repository import ChatRetrievalRepository
from database.repositories.chat_session_repository import ChatSessionRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import NotFoundException, ValidationException
from models.chat_message_model import ChatMessage
from models.chat_session_model import ChatSession
from schemas.response.chat_response import ChatMessageResult, CitationSchema
from services.retrieval_service import RetrievalService
from services.safety_context_service import SafetyContextService

logger = get_logger(__name__)


def _generate_title_from_question(question: str, max_len: int = 50) -> str:
    """Generate a clean session title from the first ~50 chars of a question."""
    cleaned = question.strip()
    if len(cleaned) <= max_len:
        return cleaned
    truncated = cleaned[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."


class ChatService:
    """Orchestrates RAG chat conversations with safety grounding and audit trails."""

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        safety_service: SafetyContextService | None = None,
    ) -> None:
        self._retrieval_service = retrieval_service or RetrievalService()
        self._safety_service = safety_service or SafetyContextService()

    def create_session(self, patient_id: UUID | str, title: str | None = None, request_id: str = "") -> ChatSession:
        """Create a new chat session for a patient."""
        session_db: Session = SessionLocal(bind=get_engine())
        try:
            repo = ChatSessionRepository(session=session_db, request_id=request_id)
            return repo.create(patient_id=patient_id, title=title)
        finally:
            session_db.close()

    def send_message(
        self,
        patient_id: UUID | str,
        session_id: UUID | str | None,
        question: str,
        request_id: str = "",
    ) -> ChatMessageResult:
        """Process a patient question through RAG retrieval, safety checking, and LLM generation."""
        if not question or not question.strip():
            raise ValidationException("Question cannot be empty")

        logger.info(
            "Chat message received",
            patient_id=str(patient_id),
            session_id=str(session_id) if session_id else "new_session",
            request_id=request_id,
        )

        session_db: Session = SessionLocal(bind=get_engine())
        try:
            session_repo = ChatSessionRepository(session=session_db, request_id=request_id)
            msg_repo = ChatMessageRepository(session=session_db, request_id=request_id)
            retrieval_repo = ChatRetrievalRepository(session=session_db, request_id=request_id)

            if session_id is None:
                title = _generate_title_from_question(question)
                chat_session = session_repo.create(patient_id=patient_id, title=title)
            else:
                chat_session = session_repo.get_by_id(session_id=session_id, patient_id=patient_id)
                if not chat_session:
                    raise NotFoundException("Chat session not found or access denied")

            user_msg = msg_repo.create(
                session_id=chat_session.session_id,
                role=MessageRole.USER,
                content=question.strip(),
            )

            all_session_msgs = msg_repo.list_by_session(
                session_id=chat_session.session_id,
                limit=MAX_CHAT_HISTORY_MESSAGES + 1,
            )
            prior_msgs = [m for m in all_session_msgs if str(m.message_id) != str(user_msg.message_id)][-MAX_CHAT_HISTORY_MESSAGES:]
            history_dicts = [{"role": str(m.role), "content": str(m.content)} for m in prior_msgs]

            state_input = {
                "patient_id": str(patient_id),
                "session_id": str(chat_session.session_id),
                "question": question.strip(),
                "conversation_history": history_dicts,
            }
            result_state = build_chat_graph().invoke(state_input)
            answer = result_state.get("answer", NO_INFO_FALLBACK_MESSAGE)
            conflicts = self._safety_service.check_drug_interactions(patient_id=patient_id, session=session_db)
            if conflicts and "DRUG INTERACTION WARNING" not in answer:
                relevant_conflicts = [
                    c for c in conflicts
                    if str(c.get('drug_a', '')).lower() in question.lower()
                    or str(c.get('drug_b', '')).lower() in question.lower()
                    or str(c.get('drug_a', '')).lower() in answer.lower()
                    or str(c.get('drug_b', '')).lower() in answer.lower()
                    or any(w in question.lower() for w in ("interact", "together", "conflict"))
                ]
                if relevant_conflicts:
                    warnings_list = [
                        f"⚠️ DRUG INTERACTION WARNING ({str(c.get('severity', 'unknown')).upper()}): "
                        f"Potential interaction detected between **{str(c.get('drug_a', '')).title()}** and **{str(c.get('drug_b', '')).title()}**. "
                        f"{str(c.get('description', ''))} Please consult your doctor or pharmacist immediately."
                        for c in relevant_conflicts
                    ]
                    answer = answer.rstrip() + "\n\n---\n\n" + "\n\n".join(warnings_list)
            citations_raw = result_state.get("citations", [])
            citations_list = [
                CitationSchema(
                    document_id=str(c.get("document_id", "")),
                    chunk_type=str(c.get("chunk_type", "")),
                    score=float(c.get("score", 0.0)),
                )
                for c in citations_raw
            ]
            valid_chunks = result_state.get("retrieved_chunks", [])
            fallback_taken = len(valid_chunks) == 0 and result_state.get("intent") == "medical_qa"

            citations_payload = [
                {"document_id": str(c.document_id), "chunk_type": str(c.chunk_type), "score": float(c.score)}
                for c in citations_list
            ]
            assistant_msg = msg_repo.create(
                session_id=chat_session.session_id,
                role=MessageRole.ASSISTANT,
                content=answer,
                citations=citations_payload,
                metadata={"model": CHAT_MODEL, "chunks_used": len(valid_chunks), "intent": result_state.get("intent", "medical_qa")},
            )

            if not fallback_taken and valid_chunks:
                retrievals_payload = [
                    {
                        "source_document_id": c.document_id,
                        "chunk_id": c.chunk_id,
                        "score": c.score,
                        "retrieved_text": c.text,
                    }
                    for c in valid_chunks
                ]
                retrieval_repo.bulk_create(message_id=assistant_msg.message_id, retrievals=retrievals_payload)

            session_repo.touch_updated_at(session_id=chat_session.session_id)

            logger.info(
                "Chat message processed successfully",
                patient_id=str(patient_id),
                session_id=str(chat_session.session_id),
                intent=result_state.get("intent", "medical_qa"),
                retrieved_chunk_count=len(valid_chunks),
                fallback_taken=fallback_taken,
                request_id=request_id,
            )

            return ChatMessageResult(
                session_id=chat_session.session_id,
                message_id=assistant_msg.message_id,
                answer=answer,
                citations=citations_list,
                created_at=assistant_msg.created_at,
            )
        finally:
            session_db.close()

    def list_sessions(
        self,
        patient_id: UUID | str,
        limit: int = 20,
        offset: int = 0,
        request_id: str = "",
    ) -> list[ChatSession]:
        """List paginated chat sessions for a patient ordered by recent activity."""
        session_db: Session = SessionLocal(bind=get_engine())
        try:
            repo = ChatSessionRepository(session=session_db, request_id=request_id)
            return repo.list_by_patient(patient_id=patient_id, limit=limit, offset=offset)
        finally:
            session_db.close()

    def get_session_messages(
        self,
        patient_id: UUID | str,
        session_id: UUID | str,
        limit: int = 50,
        request_id: str = "",
    ) -> list[ChatMessage]:
        """Fetch chat history for a specific patient session."""
        session_db: Session = SessionLocal(bind=get_engine())
        try:
            session_repo = ChatSessionRepository(session=session_db, request_id=request_id)
            chat_session = session_repo.get_by_id(session_id=session_id, patient_id=patient_id)
            if not chat_session:
                raise NotFoundException("Chat session not found or access denied")
            msg_repo = ChatMessageRepository(session=session_db, request_id=request_id)
            return msg_repo.list_by_session(session_id=session_id, limit=limit)
        finally:
            session_db.close()
