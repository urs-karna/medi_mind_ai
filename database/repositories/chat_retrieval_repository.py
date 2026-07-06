"""Chat retrieval repository operations for grounding audit trails."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.repositories.base_repository import BaseRepository
from models.chat_retrieval_model import ChatRetrieval

logger = get_logger(__name__)


class ChatRetrievalRepository(BaseRepository[ChatRetrieval]):
    """Provides bulk insert operations for chat vector retrieval audit records."""

    def __init__(self, session: Session, request_id: str = "") -> None:
        super().__init__(ChatRetrieval, session, request_id)

    def bulk_create(self, message_id: Any, retrievals: list[dict[str, Any]]) -> None:
        """Bulk insert vector retrieval audit records for an assistant message."""
        if not retrievals:
            return

        def _bulk():
            instances: list[ChatRetrieval] = []
            for r in retrievals:
                doc_id = r.get("source_document_id") or r.get("document_id")
                chunk_id = r.get("chunk_id")
                score = r.get("score")
                text = r.get("retrieved_text") or r.get("text")
                instances.append(
                    ChatRetrieval(
                        message_id=message_id,
                        source_document_id=doc_id,
                        chunk_id=str(chunk_id) if chunk_id is not None else None,
                        score=float(score) if score is not None else None,
                        retrieved_text=str(text) if text is not None else None,
                    )
                )
            self._session.add_all(instances)
            self._session.commit()

        self._execute("bulk_create", _bulk)
        logger.info("Bulk created chat retrievals", message_id=str(message_id), count=len(retrievals))
