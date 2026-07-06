"""Verification script for Phase 6 Part C: Deterministic Drug Interaction Checker & Manual Medication Entry."""

from __future__ import annotations

import sys
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import get_engine
from database.repositories.medication_repository import MedicationRepository
from database.session import SessionLocal
from helpers.drug_normalizer import normalize_drug_name
from models.medication_model import Medication
from models.patient_model import Patient
from services.chat_service import ChatService
from services.safety_context_service import SafetyContextService


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
        safety_service = SafetyContextService()

        print("\n1. Testing Manual Medication Creation...")
        med1 = repo.create_manual(
            patient_id=patient_id,
            drug_name_raw="diclofenac",
            drug_name_normalized=normalize_drug_name("diclofenac"),
            dosage="50mg",
            frequency="Twice daily",
        )
        med2 = repo.create_manual(
            patient_id=patient_id,
            drug_name_raw="metformin",
            drug_name_normalized=normalize_drug_name("metformin"),
            dosage="500mg",
            frequency="Once daily",
        )
        print(f"Created manual medication 1: {med1.drug_name_normalized} (source: {med1.entry_source})")
        print(f"Created manual medication 2: {med2.drug_name_normalized} (source: {med2.entry_source})")

        print("\n2. Testing GET Medications (list_by_patient)...")
        all_meds = repo.list_by_patient(patient_id=patient_id)
        print(f"Total medications retrieved: {len(all_meds)}")
        for m in all_meds[:5]:
            print(f" - {m.drug_name_normalized} | Status: {m.status} | Source: {m.entry_source}")

        print("\n3. Testing Deterministic Drug Interaction Check...")
        conflicts = safety_service.check_drug_interactions(patient_id=patient_id, session=session)
        print(f"Detected conflicts count: {len(conflicts)}")
        for c in conflicts:
            print(f" - [{c['severity'].upper()}] {c['drug_a']} + {c['drug_b']}: {c['description']}")
        assert len(conflicts) >= 1, "Expected at least one conflict between Diclofenac and Metformin!"

        print("\n4. Testing Chat Service Integration (Known Interaction Warning)...")
        chat_service = ChatService()
        res1 = chat_service.send_message(
            patient_id=patient_id,
            session_id=None,
            question="Can I take Diclofenac and Metformin together?"
        )
        print("--- Chat Response (Known Interaction) ---")
        print(res1.answer)
        assert "DRUG INTERACTION WARNING" in res1.answer, "Expected DRUG INTERACTION WARNING in chat response!"

        print("\n5. Testing Chat Service Integration (Unverified Medication Suggestion)...")
        res2 = chat_service.send_message(
            patient_id=patient_id,
            session_id=None,
            question="Is it safe for me to start taking Lisinopril for my blood pressure?"
        )
        print("--- Chat Response (Unverified Medication) ---")
        print(res2.answer)

        print("\n6. Testing DELETE / Discontinue Medication...")
        med1.status = "DISCONTINUED"
        repo.update(med1)
        med2.status = "DISCONTINUED"
        repo.update(med2)
        print("Marked test medications as DISCONTINUED.")

        print("\n--- Phase 6 Part C Verification Successfully Completed! ---")

    finally:
        session.close()


if __name__ == "__main__":
    main()
