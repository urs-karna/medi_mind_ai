"""Drug name normalization utility functions."""

from __future__ import annotations

# V2 will replace this with RxNorm cross-check; see medications.rxnorm_code migration note in schema doc.
COMMON_OCR_DRUG_FIXES: dict[str, str] = {
    "metfornin": "Metformin",
    "amoxilin": "Amoxicillin",
    "amoxcillin": "Amoxicillin",
    "paracetmol": "Paracetamol",
    "lipitr": "Lipitor",
    "lisinoprl": "Lisinopril",
}


def normalize_drug_name(raw: str | None) -> str | None:
    """Clean, title-case, and normalize raw OCR extracted drug names."""
    if raw is None:
        return None
    cleaned = " ".join(raw.strip().split()).title()
    if not cleaned:
        return None
    lookup = cleaned.lower()
    return COMMON_OCR_DRUG_FIXES.get(lookup, cleaned)
