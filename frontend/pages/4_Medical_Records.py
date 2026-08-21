"""Medical Records page for MediMind AI (Prescriptions and Lab Reports)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(page_title="Medical Records - MediMind AI", page_icon="📑", layout="wide")

# Ensure session state variables exist
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "rx_offset" not in st.session_state:
    st.session_state["rx_offset"] = 0
if "lab_offset" not in st.session_state:
    st.session_state["lab_offset"] = 0


def render_prescriptions_tab() -> None:
    """Render the Prescriptions tab with expandable cards and medication lists."""
    st.subheader("💊 Prescriptions History")
    limit = 20
    offset = st.session_state.get("rx_offset", 0)

    try:
        res = api_client.get("/records/prescriptions", params={"limit": limit, "offset": offset}, auth=True)
        rxs: list[dict[str, Any]] = res.get("data") or []

        if not rxs and offset == 0:
            st.info("No prescription records found.")
        else:
            for rx in rxs:
                doc_name = rx.get("doctor_name") or "Unknown Doctor"
                date_str = str(rx.get("prescribed_date") or "Unknown Date")
                diagnosis = rx.get("diagnosis") or []
                diag_str = ", ".join(diagnosis) if diagnosis else "None recorded"

                with st.expander(f"🩺 Prescription from **{doc_name}** — `{date_str}`", expanded=True):
                    st.markdown(f"**Diagnosis**: {diag_str}")
                    meds = rx.get("medications") or []
                    if meds:
                        st.markdown("**Prescribed Medications:**")
                        for med in meds:
                            name = med.get("drug_name_normalized") or "Unknown Medication"
                            dosage = med.get("dosage") or ""
                            freq = med.get("frequency") or ""
                            instr = med.get("instructions") or ""
                            details = [d for d in [dosage, freq, instr] if d]
                            details_str = f" — *{' | '.join(details)}*" if details else ""
                            st.markdown(f"- **{name}**{details_str}")
                    else:
                        st.caption("No specific medications listed.")

            col_prev, col_next = st.columns(2)
            with col_prev:
                if offset > 0:
                    if st.button("⬅️ Previous Prescriptions", key="rx_prev"):
                        st.session_state["rx_offset"] = max(0, offset - limit)
                        st.rerun()
            with col_next:
                if len(rxs) == limit:
                    if st.button("Load More Prescriptions ➡️", key="rx_next"):
                        st.session_state["rx_offset"] = offset + limit
                        st.rerun()

    except Exception as exc:
        st.error(f"Failed to fetch prescriptions: {exc}")


def render_lab_reports_tab() -> None:
    """Render the Lab Reports tab with color-highlighted dataframe and pagination."""
    st.subheader("🧪 Laboratory Test Results")
    limit = 20
    offset = st.session_state.get("lab_offset", 0)

    try:
        res = api_client.get("/records/lab-results", params={"limit": limit, "offset": offset}, auth=True)
        labs: list[dict[str, Any]] = res.get("data") or []

        if not labs and offset == 0:
            st.info("No laboratory test results found.")
        else:
            table_data = []
            for lab in labs:
                table_data.append({
                    "Test Name": lab.get("test_name") or "Unknown Test",
                    "Value": lab.get("value", ""),
                    "Unit": lab.get("unit") or "",
                    "Reference Range": lab.get("reference_range") or "",
                    "Flag": lab.get("flag") or "Normal",
                    "Test Date": str(lab.get("test_date") or ""),
                })

            df = pd.DataFrame(table_data)

            def highlight_flag(row: pd.Series) -> list[str]:
                flag_val = str(row.get("Flag", "")).lower()
                if flag_val and flag_val not in ("normal", "none", "", "nan"):
                    return ["background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold"] * len(row)
                return [""] * len(row)

            try:
                styled_df = df.style.apply(highlight_flag, axis=1)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            except Exception:
                st.dataframe(df, use_container_width=True, hide_index=True)

            col_prev, col_next = st.columns(2)
            with col_prev:
                if offset > 0:
                    if st.button("⬅️ Previous Results", key="lab_prev"):
                        st.session_state["lab_offset"] = max(0, offset - limit)
                        st.rerun()
            with col_next:
                if len(labs) == limit:
                    if st.button("Load More Results ➡️", key="lab_next"):
                        st.session_state["lab_offset"] = offset + limit
                        st.rerun()

    except Exception as exc:
        st.error(f"Failed to fetch lab results: {exc}")


def render_medical_records() -> None:
    """Render the Medical Records page with Prescriptions and Lab Reports tabs."""
    if not st.session_state.get("access_token"):
        st.warning("Please log in to access Medical Records.")
        st.switch_page("pages/1_Login.py")
        return

    st.title("📑 Structured Medical Records")
    st.markdown("Browse and review your extracted clinical history organized by record category.")

    tab_rx, tab_lab = st.tabs(["💊 Prescriptions", "🧪 Lab Reports"])
    with tab_rx:
        render_prescriptions_tab()
    with tab_lab:
        render_lab_reports_tab()


if __name__ == "__main__":
    render_medical_records()
