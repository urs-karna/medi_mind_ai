"""RAG ingestion service orchestrating chunking, embedding, and Pinecone vector upsertion."""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.embedding_client import embed_texts
from agents.pinecone_client import delete_vectors_by_document, upsert_vectors
from app_logging.logger import get_logger
from config.constants import (
    DOCUMENT_TYPE_LAB_REPORT,
    DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN,
    DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
)
from database.connection import get_engine
from database.repositories.document_repository import DocumentRepository
from database.session import SessionLocal
from exceptions.custom_exceptions import NotFoundException, RAGIngestionException
from models.doctor_model import Doctor
from models.lab_result_model import LabResult
from models.medication_model import Medication
from models.prescription_model import Prescription
from services.chunking_service import ChunkInput, build_lab_result_chunks, build_medication_chunks

logger = get_logger(__name__)


class RAGIngestionService:
    """Orchestrates entity chunking, vector embedding, and Pinecone database storage."""

    def ingest_document(
        self,
        document_id: uuid.UUID | str,
        patient_id: uuid.UUID | str,
        request_id: str = "",
    ) -> dict[str, int]:
        """Ingest document entities into Pinecone vector index idempotently."""
        if not patient_id:
            raise RAGIngestionException("patient_id is strictly required for RAG ingestion")
        if not document_id:
            raise RAGIngestionException("document_id is strictly required for RAG ingestion")

        doc_id_str = str(document_id)
        pat_id_str = str(patient_id)

        # 1. Idempotent cleanup of existing vectors for this document
        logger.info(
            "Starting vector cleanup for document",
            document_id=doc_id_str,
            patient_id=pat_id_str,
            request_id=request_id,
        )
        delete_vectors_by_document(document_id=doc_id_str, patient_id=pat_id_str)

        session: Session = SessionLocal(bind=get_engine())
        chunks: list[ChunkInput] = []

        try:
            # 2. Fetch document row patient-scoped
            doc_repo = DocumentRepository(session=session, request_id=request_id)
            doc = doc_repo.get_by_id(document_id=document_id, patient_id=patient_id)
            if not doc:
                raise NotFoundException("Document not found for RAG ingestion")

            doc_type = doc.document_type or ""

            # 3. Build entity chunks based on document type
            if doc_type in (DOCUMENT_TYPE_PRESCRIPTION_PRINTED, DOCUMENT_TYPE_PRESCRIPTION_HANDWRITTEN):
                prescriptions = session.scalars(
                    select(Prescription).filter_by(document_id=doc.document_id, patient_id=doc.patient_id)
                ).all()
                for presc in prescriptions:
                    doctor = None
                    if presc.doctor_id:
                        doctor = session.get(Doctor, presc.doctor_id)
                    meds = session.scalars(
                        select(Medication).filter_by(prescription_id=presc.prescription_id, patient_id=doc.patient_id)
                    ).all()
                    presc_chunks = build_medication_chunks(
                        prescription=presc,
                        doctor=doctor,
                        medications=list(meds),
                        patient_id=doc.patient_id,
                        document_id=doc.document_id,
                    )
                    chunks.extend(presc_chunks)
            elif doc_type == DOCUMENT_TYPE_LAB_REPORT:
                labs = session.scalars(
                    select(LabResult).filter_by(document_id=doc.document_id, patient_id=doc.patient_id)
                ).all()
                lab_chunks = build_lab_result_chunks(
                    lab_results=list(labs),
                    document=doc,
                    patient_id=doc.patient_id,
                    document_id=doc.document_id,
                )
                chunks.extend(lab_chunks)
            else:
                logger.info(
                    "Skipping chunk building for document type without persistence path",
                    document_type=doc_type,
                    document_id=doc_id_str,
                    request_id=request_id,
                )
        finally:
            session.close()

        chunk_count = len(chunks)
        logger.info(
            "Built total entity chunks for document",
            chunk_count=chunk_count,
            document_id=doc_id_str,
            patient_id=pat_id_str,
            request_id=request_id,
        )

        if chunk_count == 0:
            return {"chunks_created": 0}

        # 4. Embed all chunk texts in one batched call
        start_time = time.perf_counter()
        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts)
        embed_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Embedded chunk texts",
            chunk_count=chunk_count,
            embed_latency_ms=embed_latency_ms,
            request_id=request_id,
        )

        # 5. Upsert via client wrapper
        vectors_to_upsert: list[dict[str, Any]] = []
        for chunk, vector in zip(chunks, embeddings):
            vectors_to_upsert.append({
                "id": chunk.chunk_id,
                "values": vector,
                "metadata": chunk.metadata,
            })

        upsert_vectors(vectors_to_upsert)
        logger.info(
            "Upserted entity chunks to Pinecone",
            upsert_count=len(vectors_to_upsert),
            document_id=doc_id_str,
            patient_id=pat_id_str,
            request_id=request_id,
        )

        # 6. Return created count
        return {"chunks_created": chunk_count}
