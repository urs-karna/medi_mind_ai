"""Service layer for retrieving patient safety context (allergies and chronic conditions)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app_logging.logger import get_logger
from database.connection import get_engine
from database.repositories.base_repository import BaseRepository
from database.session import SessionLocal
from models.drug_interaction_model import DrugInteraction
from models.medication_model import Medication
from models.patient_allergy_model import PatientAllergy
from models.patient_chronic_condition_model import PatientChronicCondition

logger = get_logger(__name__)


class SafetyContextService:
    """Retrieves recorded allergies and chronic conditions for prompt safety grounding."""

    def get_safety_context(
        self,
        patient_id: UUID | str,
        session: Session | None = None,
        request_id: str = "",
    ) -> dict[str, list[str]]:
        """Fetch recorded allergies and chronic conditions as plain string lists."""
        close_session = False
        if session is None:
            session = SessionLocal(bind=get_engine())
            close_session = True

        try:
            allergy_repo = BaseRepository(PatientAllergy, session, request_id)
            condition_repo = BaseRepository(PatientChronicCondition, session, request_id)

            allergies_rows = allergy_repo.list_by_patient_id(patient_id)
            conditions_rows = condition_repo.list_by_patient_id(patient_id)

            allergies: list[str] = []
            for a in allergies_rows:
                if a.allergen:
                    desc = str(a.allergen)
                    if a.reaction:
                        desc += f" (reaction: {a.reaction})"
                    allergies.append(desc)

            chronic_conditions: list[str] = []
            for c in conditions_rows:
                if c.condition_name:
                    desc = str(c.condition_name)
                    if c.status:
                        desc += f" ({c.status})"
                    chronic_conditions.append(desc)

            return {
                "allergies": allergies,
                "chronic_conditions": chronic_conditions,
            }
        finally:
            if close_session:
                session.close()

    def check_drug_interactions(
        self,
        patient_id: UUID | str,
        session: Session | None = None,
    ) -> list[dict[str, Any]]:
        """Check active medications against known pairwise drug-drug interactions."""
        close_session = False
        if session is None:
            session = SessionLocal(bind=get_engine())
            close_session = True

        try:
            meds = session.scalars(
                select(Medication).filter(
                    Medication.patient_id == str(patient_id),
                    sa.func.upper(Medication.status) == "ACTIVE",
                )
            ).all()
            active_drug_names = []
            for m in meds:
                name = m.drug_name_normalized or m.drug_name_raw
                if name:
                    active_drug_names.append(name.strip().lower())
            active_drug_names = list(set(active_drug_names))

            if len(active_drug_names) < 2:
                return []

            all_interactions = session.scalars(select(DrugInteraction)).all()
            conflicts = []
            seen_pairs = set()

            for i in range(len(active_drug_names)):
                for j in range(i + 1, len(active_drug_names)):
                    d1 = active_drug_names[i]
                    d2 = active_drug_names[j]
                    for ix in all_interactions:
                        ia = ix.drug_a_normalized.strip().lower()
                        ib = ix.drug_b_normalized.strip().lower()
                        if (d1 == ia and d2 == ib) or (d1 == ib and d2 == ia):
                            pair_key = tuple(sorted([d1, d2]))
                            if pair_key not in seen_pairs:
                                seen_pairs.add(pair_key)
                                conflicts.append({
                                    "drug_a": d1,
                                    "drug_b": d2,
                                    "severity": ix.severity or "unknown",
                                    "description": ix.description or "Potential interaction detected.",
                                })
            return conflicts
        finally:
            if close_session:
                session.close()
