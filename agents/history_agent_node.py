"""History Agent node for direct structured database enumeration queries and deterministic safety gate checks."""

from __future__ import annotations
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agents.graph_state import ChatGraphState
from app_logging.logger import get_logger
from config.constants import LAB_HISTORY_KEYWORDS, PRESCRIPTION_HISTORY_KEYWORDS
from database.connection import get_engine
from database.repositories.base_repository import BaseRepository
from database.session import SessionLocal
from models.doctor_model import Doctor
from models.lab_result_model import LabResult
from models.patient_chronic_condition_model import PatientChronicCondition
from models.prescription_model import Prescription
from services.safety_context_service import SafetyContextService

logger = get_logger(__name__)


def _classify_target_entity(question_lower: str) -> str:
    """Classify target entity based on keyword presence."""
    has_lab = any(kw in question_lower for kw in LAB_HISTORY_KEYWORDS)
    has_rx = any(kw in question_lower for kw in PRESCRIPTION_HISTORY_KEYWORDS)
    if has_lab and not has_rx:
        return "lab_results"
    if has_rx and not has_lab:
        return "prescriptions"
    return "both"


def _query_and_format_prescriptions(
    session: Session,
    patient_id: str,
    question_lower: str,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Query prescriptions and format deterministically with allergy safety checks."""
    condition_repo = BaseRepository(PatientChronicCondition, session)
    chronic_conditions = condition_repo.list_by_patient_id(patient_id)
    candidate_keywords = set()
    for cc in chronic_conditions:
        if cc.condition_name:
            candidate_keywords.add(cc.condition_name.strip())

    all_rows = session.execute(
        select(Prescription, Doctor)
        .outerjoin(Doctor, Prescription.doctor_id == Doctor.doctor_id)
        .options(selectinload(Prescription.medications))
        .filter(Prescription.patient_id == patient_id)
        .order_by(Prescription.prescribed_date.desc().nulls_last())
        .limit(50)
    ).all()

    for rx, _ in all_rows:
        if rx.diagnosis:
            for diag in rx.diagnosis:
                if diag:
                    candidate_keywords.add(diag.strip())

    matched_keyword = None
    for kw in candidate_keywords:
        if kw and len(kw) > 2 and kw.lower() in question_lower:
            matched_keyword = kw
            break

    if matched_keyword:
        filtered_rows = [
            (rx, doc)
            for rx, doc in all_rows
            if rx.diagnosis and any(matched_keyword.lower() in d.lower() for d in rx.diagnosis if d)
        ][:20]
    else:
        filtered_rows = all_rows[:20]

    if not filtered_rows:
        if matched_keyword:
            summary_text = f"No prescriptions found in your medical history matching '{matched_keyword}'."
        else:
            summary_text = "You currently have no prescriptions recorded in your medical history."
        return summary_text, [], []

    lines = []
    if matched_keyword:
        lines.append(f"Here is your prescription history related to **{matched_keyword}**:\n")
    else:
        lines.append("Here is your complete prescription history:\n")

    seen_docs = set()
    citations = []
    mentioned_medications = []

    for idx, (rx, doc) in enumerate(filtered_rows, start=1):
        date_str = rx.prescribed_date.strftime("%B %d, %Y") if rx.prescribed_date else "Date not recorded"
        doc_str = doc.name if doc and doc.name else "Doctor not recorded"
        diag_str = ", ".join(rx.diagnosis) if rx.diagnosis else "No diagnosis recorded"

        lines.append(f"### Prescription {idx} — {date_str}")
        lines.append(f"- **Doctor**: {doc_str}")
        lines.append(f"- **Diagnosis**: {diag_str}")

        if rx.medications:
            med_lines = []
            for m in rx.medications:
                med_name = m.drug_name_normalized or m.drug_name_raw or "Unnamed medication"
                mentioned_medications.append(med_name)
                details = [med_name]
                if m.dosage:
                    details.append(f"{m.dosage}")
                if m.frequency:
                    details.append(f"({m.frequency})")
                med_lines.append(" ".join(details))
            lines.append(f"- **Medications**: {', '.join(med_lines)}")
        else:
            lines.append("- **Medications**: None listed")
        lines.append("")

        if rx.document_id and str(rx.document_id) not in seen_docs:
            seen_docs.add(str(rx.document_id))
            citations.append({
                "document_id": str(rx.document_id),
                "chunk_type": "prescription_history",
                "score": 1.0,
            })

    safety_service = SafetyContextService()
    safety_context = safety_service.get_safety_context(patient_id=patient_id, session=session)
    allergies = safety_context.get("allergies", [])

    warnings = set()
    for med in mentioned_medications:
        if not med:
            continue
        med_lower = med.lower()
        for allergy_str in allergies:
            allergen_name = allergy_str.split(" (reaction:")[0].strip().lower()
            if allergen_name and (allergen_name in med_lower or med_lower in allergen_name):
                warnings.add(
                    f"⚠️ SAFETY WARNING: You have a recorded allergy to **{allergy_str}**, "
                    f"which may conflict with **{med}**. Please consult your doctor before taking this medication."
                )

    conflicts = safety_service.check_drug_interactions(patient_id=patient_id, session=session)
    for c in conflicts:
        warnings.add(
            f"⚠️ DRUG INTERACTION WARNING ({str(c.get('severity', 'unknown')).upper()}): "
            f"Potential interaction detected between **{str(c.get('drug_a', '')).title()}** and **{str(c.get('drug_b', '')).title()}**. "
            f"{str(c.get('description', ''))} Please consult your doctor or pharmacist immediately."
        )

    if warnings:
        lines.append("\n" + "\n\n".join(warnings))

    summary_text = "\n".join(lines).strip()
    structured = [
        {
            "prescription_id": str(rx.prescription_id),
            "prescribed_date": str(rx.prescribed_date) if rx.prescribed_date else None,
            "doctor": doc.name if doc else None,
            "diagnosis": rx.diagnosis,
        }
        for rx, doc in filtered_rows
    ]
    return summary_text, citations, structured


def _query_and_format_lab_results(
    session: Session,
    patient_id: str,
    question_lower: str,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Query lab results and format deterministically with graceful fallback."""
    all_lab_rows = session.scalars(
        select(LabResult)
        .filter(LabResult.patient_id == patient_id)
        .order_by(LabResult.test_date.desc().nulls_last())
        .limit(50)
    ).all()

    candidate_test_names = {row.test_name.strip() for row in all_lab_rows if row.test_name}
    matched_test_name = None
    for tname in candidate_test_names:
        if len(tname) > 2 and tname.lower() in question_lower:
            matched_test_name = tname
            break

    if matched_test_name:
        filtered_labs = [row for row in all_lab_rows if row.test_name and matched_test_name.lower() in row.test_name.lower()][:20]
    else:
        filtered_labs = all_lab_rows[:20]

    if not filtered_labs:
        return "You currently have no lab results recorded in your medical history.", [], []

    lines = []
    if matched_test_name:
        lines.append(f"Here are your lab results related to **{matched_test_name}**:\n")
    else:
        lines.append("Here is your complete lab reports history:\n")

    seen_docs = set()
    citations = []
    structured = []

    for row in filtered_labs:
        test_name = row.test_name or "Unnamed test"
        val_str = str(row.value) if row.value is not None else "N/A"
        unit_str = row.unit or ""
        ref_str = row.reference_range or "Not specified"
        flag_str = row.flag or "Normal"
        date_str = row.test_date.strftime("%Y-%m-%d") if row.test_date else "Date not recorded"

        lines.append(f"- **{test_name}**: {val_str} {unit_str} (reference range: {ref_str}, flag: {flag_str}) — {date_str}")

        if row.document_id and str(row.document_id) not in seen_docs:
            seen_docs.add(str(row.document_id))
            citations.append({
                "document_id": str(row.document_id),
                "chunk_type": "lab_history",
                "score": 1.0,
            })
        structured.append({
            "id": str(row.id),
            "test_name": test_name,
            "value": float(row.value) if row.value is not None else None,
            "unit": unit_str,
            "flag": flag_str,
            "test_date": date_str,
        })

    return "\n".join(lines).strip(), citations, structured


def run_history_query(state: ChatGraphState) -> ChatGraphState:
    """Execute direct structured DB query for medical history enumeration and apply safety gate."""
    patient_id = state.get("patient_id", "")
    question_lower = state.get("question", "").lower()

    session: Session = SessionLocal(bind=get_engine())
    try:
        target_entity = _classify_target_entity(question_lower)

        if target_entity == "prescriptions":
            answer_text, citations, structured = _query_and_format_prescriptions(session, patient_id, question_lower)
        elif target_entity == "lab_results":
            answer_text, citations, structured = _query_and_format_lab_results(session, patient_id, question_lower)
        else:
            rx_text, rx_citations, rx_structured = _query_and_format_prescriptions(session, patient_id, question_lower)
            lab_text, lab_citations, lab_structured = _query_and_format_lab_results(session, patient_id, question_lower)

            answer_text = f"## Prescriptions\n\n{rx_text}\n\n---\n\n## Lab Reports\n\n{lab_text}"

            seen_cits = set()
            citations = []
            for c in rx_citations + lab_citations:
                key = (c["document_id"], c["chunk_type"])
                if key not in seen_cits:
                    seen_cits.add(key)
                    citations.append(c)

            structured = rx_structured + lab_structured

        state["answer"] = answer_text
        state["citations"] = citations
        state["structured_results"] = structured

        logger.info(
            "History agent query executed",
            path="history_query",
            target_entity=target_entity,
            patient_id=str(patient_id),
            result_count=len(structured),
        )
        return state
    finally:
        session.close()
