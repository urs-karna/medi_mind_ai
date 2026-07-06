"""Test script for Phase 6 Part B.2 LangGraph router keyword matching and explanation overrides."""

from __future__ import annotations

import sys
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import get_engine
from database.session import SessionLocal
from models.patient_model import Patient
from models.prescription_model import Prescription
from services.chat_service import ChatService


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    session: Session = SessionLocal(bind=get_engine())
    try:
        rx = session.scalars(select(Prescription).filter(Prescription.patient_id.is_not(None))).first()
        if rx and rx.patient_id:
            patient_id = rx.patient_id
            print(f"Using Patient ID from prescription: {patient_id}")
        else:
            patient = session.scalars(select(Patient)).first()
            if not patient:
                print("No patients found in DB.")
                return
            patient_id = patient.patient_id
            print(f"Using Patient ID: {patient_id}")

        chat_service = ChatService()

        print("\n" + "=" * 60)
        print("TEST 1: 'show the lab_report test data' (History Agent Lab Panel)")
        print("=" * 60)
        res1 = chat_service.send_message(patient_id=patient_id, session_id=None, question="show the lab_report test data")
        print(f"Answer:\n{res1.answer}")
        print(f"Citations count: {len(res1.citations)}")
        for c in res1.citations:
            print(f"  Citation: chunk_type={c.chunk_type}, score={c.score}")

        print("\n" + "=" * 60)
        print("TEST 2: 'show the lab_report test data of my blood cancer' (Graceful Fallback)")
        print("=" * 60)
        res2 = chat_service.send_message(patient_id=patient_id, session_id=None, question="show the lab_report test data of my blood cancer")
        print(f"Answer:\n{res2.answer}")
        print(f"Citations count: {len(res2.citations)}")
        for c in res2.citations:
            print(f"  Citation: chunk_type={c.chunk_type}, score={c.score}")

        print("\n" + "=" * 60)
        print("TEST 3: 'is it safe for me to take my medication together' (Explanation Override -> RAG)")
        print("=" * 60)
        res3 = chat_service.send_message(patient_id=patient_id, session_id=None, question="is it safe for me to take my medication together")
        print(f"Answer:\n{res3.answer}")
        print(f"Citations count: {len(res3.citations)}")
        for c in res3.citations:
            print(f"  Citation: chunk_type={c.chunk_type}, score={c.score}")

    finally:
        session.close()


if __name__ == "__main__":
    main()
