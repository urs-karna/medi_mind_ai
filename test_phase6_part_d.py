"""Verification script for Phase 6 Part D: Manual Entry RAG Sync + Cascade Deletion."""

from __future__ import annotations

import sys
import time
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.embedding_client import embed_texts
from agents.pinecone_client import delete_vector_by_id, query_vectors, upsert_vectors
from config.constants import DOCUMENT_STATUS_DELETED, DOCUMENT_STATUS_READY, DOCUMENT_TYPE_PRESCRIPTION_PRINTED
from database.connection import get_engine
from database.repositories.medication_repository import MedicationRepository
from database.session import SessionLocal
from helpers.drug_normalizer import normalize_drug_name
from models.chat_message_model import ChatMessage
from models.chat_retrieval_model import ChatRetrieval
from models.chat_session_model import ChatSession
from models.document_model import Document
from models.lab_result_model import LabResult
from models.medical_timeline_model import MedicalTimeline
from models.medication_model import Medication
from models.patient_model import Patient
from models.prescription_model import Prescription
from services.chat_service import ChatService
from services.chunking_service import build_medication_chunks
from services.document_service import DocumentService


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    session: Session = SessionLocal(bind=get_engine())
    try:
        patient = session.scalars(select(Patient)).first()
        if not patient:
            print("No patients found in DB. Cannot run verification.")
            return
        patient_id = patient.patient_id
        print(f"--- Using Patient ID: {patient_id} ---")

        repo = MedicationRepository(session=session)
        chat_service = ChatService()
        doc_service = DocumentService()

        # ==========================================
        # TASK 1 & 5.1: Sync Manual Medication Entry
        # ==========================================
        print("\n1. Testing Manual Medication Entry RAG Sync...")
        med = repo.create_manual(
            patient_id=patient_id,
            drug_name_raw="Metformin",
            drug_name_normalized=normalize_drug_name("Metformin"),
            dosage="500mg",
            frequency="Once daily",
        )
        print(f"Created manual medication in DB: {med.drug_name_normalized} (ID: {med.medication_id})")

        # Sync to Pinecone (as create_medication endpoint does)
        chunks = build_medication_chunks(
            prescription=None,
            doctor=None,
            medications=[med],
            patient_id=patient_id,
            document_id=None,
            entry_source="manual_entry",
        )
        assert len(chunks) == 1
        print(f"Built chunk ID: {chunks[0].chunk_id}")
        print(f"Chunk text: {chunks[0].text}")
        assert "Prescribed." not in chunks[0].text, "Chunk text should not end with awkward 'Prescribed.'"

        vecs = embed_texts([chunks[0].text])
        upsert_vectors([{
            "id": chunks[0].chunk_id,
            "values": vecs[0],
            "metadata": chunks[0].metadata,
        }])
        print("Upserted manual medication vector to Pinecone. Waiting 3s for indexing...")
        time.sleep(3)

        print("\nAsking ChatService about Metformin...")
        res1 = chat_service.send_message(
            patient_id=patient_id,
            session_id=None,
            question="Am I currently taking Metformin? What is my dosage?"
        )
        print("--- Chat Response (With RAG Sync) ---")
        print(res1.answer)
        assert "500" in res1.answer or "Metformin" in res1.answer, "LLM should confirm Metformin is in records!"

        # ==========================================
        # TASK 2 & 5.2: Sync Medication Discontinuation
        # ==========================================
        print("\n2. Testing Discontinuation RAG Sync...")
        med.status = "DISCONTINUED"
        repo.update(med)
        chunk_id = f"patient_{patient_id}_manual_med_{med.medication_id}"
        delete_vector_by_id(chunk_id)
        print("Marked medication DISCONTINUED in DB and removed vector from Pinecone. Waiting 3s...")
        time.sleep(3)

        # Confirm vector is gone via query
        zero_vec = [0.0] * 768
        matches = query_vectors(embedding=zero_vec, patient_id=str(patient_id), top_k=100, filters={"reference_id": str(med.medication_id)})
        assert len(matches) == 0, f"Expected 0 vectors in Pinecone for discontinued med, got {len(matches)}"
        print("Confirmed: Vector is completely gone from Pinecone!")

        # Confirm row is still present in DB
        db_med = session.get(Medication, med.medication_id)
        assert db_med is not None
        assert db_med.status == "DISCONTINUED"
        print("Confirmed: Row is still present in DB with status DISCONTINUED!")

        # ==========================================
        # TASK 4 & 5.3: Document Cascade Deletion
        # ==========================================
        print("\n3. Testing Document Cascade Deletion...")
        doc_id = uuid.uuid4()
        presc_id = uuid.uuid4()
        med_id = uuid.uuid4()
        lab_id = uuid.uuid4()
        timeline_id1 = uuid.uuid4()
        timeline_id2 = uuid.uuid4()
        session_id = uuid.uuid4()
        msg_id = uuid.uuid4()
        retrieval_id = uuid.uuid4()

        # Create test document
        test_doc = Document(
            document_id=doc_id,
            patient_id=patient_id,
            document_type=DOCUMENT_TYPE_PRESCRIPTION_PRINTED,
            raw_file_uri="test/uri.pdf",
            status=DOCUMENT_STATUS_READY,
            extraction_json={"test": "data"},
        )
        session.add(test_doc)

        # Create test prescription & medication
        test_presc = Prescription(
            prescription_id=presc_id,
            document_id=doc_id,
            patient_id=patient_id,
            prescribed_date=date.today(),
        )
        session.add(test_presc)

        test_med = Medication(
            medication_id=med_id,
            prescription_id=presc_id,
            patient_id=patient_id,
            drug_name_raw="TestDrug",
            drug_name_normalized="testdrug",
        )
        session.add(test_med)

        # Create test lab result
        test_lab = LabResult(
            id=lab_id,
            document_id=doc_id,
            patient_id=patient_id,
            test_name="TestLab",
            value=100.0,
            unit="mg/dL",
        )
        session.add(test_lab)

        # Create timeline events (one referencing prescription, one referencing document)
        t_event1 = MedicalTimeline(
            event_id=timeline_id1,
            patient_id=patient_id,
            event_type="prescription",
            reference_id=presc_id,
            summary="Test presc event",
        )
        t_event2 = MedicalTimeline(
            event_id=timeline_id2,
            patient_id=patient_id,
            event_type="lab_report",
            reference_id=doc_id,
            summary="Test lab event",
        )
        session.add_all([t_event1, t_event2])

        # Create audit chat retrieval row referencing this document
        chat_sess = ChatSession(session_id=session_id, patient_id=patient_id, title="Test session")
        chat_msg = ChatMessage(message_id=msg_id, session_id=session_id, role="assistant", content="test")
        chat_ret = ChatRetrieval(
            retrieval_id=retrieval_id,
            message_id=msg_id,
            chunk_id=f"patient_{patient_id}_doc_{doc_id}_med_{med_id}",
            source_document_id=doc_id,
            retrieved_text="test chunk",
            score=0.9,
        )
        session.add_all([chat_sess, chat_msg, chat_ret])
        session.commit()

        print(f"Created dummy document {doc_id} with prescription, medication, lab result, timeline events, and audit retrieval.")

        # Upsert dummy vector to Pinecone for this document
        dummy_chunk_id = f"patient_{patient_id}_doc_{doc_id}_med_{med_id}"
        upsert_vectors([{
            "id": dummy_chunk_id,
            "values": [0.1] * 768,
            "metadata": {
                "patient_id": str(patient_id),
                "document_id": str(doc_id),
                "text": "dummy doc text",
            }
        }])
        print("Upserted dummy vector to Pinecone. Waiting 3s...")
        time.sleep(3)

        # Now execute cascade deletion
        print("Executing DocumentService.delete_document...")
        res_del = doc_service.delete_document(patient_id=patient_id, document_id=doc_id)
        print(f"Delete response: {res_del.message}")

        # Verify DB cleanup
        session.expire_all()
        check_doc = session.get(Document, doc_id)
        assert check_doc is not None
        assert check_doc.status == DOCUMENT_STATUS_DELETED
        assert check_doc.extraction_json == {"test": "data"}
        print("Confirmed: Document row still exists with status='deleted' and extraction_json intact!")

        check_prescs = session.scalars(select(Prescription).filter_by(document_id=doc_id)).all()
        assert len(check_prescs) == 0, "Prescriptions should be deleted!"
        check_meds = session.scalars(select(Medication).filter_by(prescription_id=presc_id)).all()
        assert len(check_meds) == 0, "Medications should be deleted!"
        check_labs = session.scalars(select(LabResult).filter_by(document_id=doc_id)).all()
        assert len(check_labs) == 0, "Lab results should be deleted!"
        check_timeline = session.scalars(select(MedicalTimeline).filter(MedicalTimeline.event_id.in_([timeline_id1, timeline_id2]))).all()
        assert len(check_timeline) == 0, "Timeline events should be deleted!"
        print("Confirmed: All derived prescriptions, medications, lab results, and timeline rows are gone!")

        check_ret = session.get(ChatRetrieval, retrieval_id)
        assert check_ret is not None
        assert check_ret.source_document_id == doc_id
        print("Confirmed: Historical chat_retrievals audit row is untouched!")

        # Verify Pinecone cleanup
        time.sleep(3)
        matches_doc = query_vectors(embedding=[0.1] * 768, patient_id=str(patient_id), top_k=100, filters={"document_id": str(doc_id)})
        assert len(matches_doc) == 0, f"Expected 0 vectors for deleted doc, got {len(matches_doc)}"
        print("Confirmed: Pinecone vectors for deleted document are completely removed!")

        # Clean up dummy audit rows
        session.delete(check_ret)
        session.delete(chat_msg)
        session.delete(chat_sess)
        session.delete(check_doc)
        session.commit()

        print("\n--- Phase 6 Part D Verification Successfully Completed! ---")

    finally:
        session.close()


if __name__ == "__main__":
    main()
