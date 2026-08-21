"""Upload Center page for MediMind AI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(page_title="Upload Center - MediMind AI", page_icon="📂", layout="wide")

# Ensure session state variables exist
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "doc_offset" not in st.session_state:
    st.session_state["doc_offset"] = 0

DOCUMENT_TYPES = [
    "prescription_printed",
    "prescription_handwritten",
    "lab_report",
    "drug_package",
    "medical_bill",
    "discharge_summary",
    "insurance_document",
    "medical_record",
]


def render_status_badge(status: str | None) -> None:
    """Render a colored status banner based on processing state."""
    if not status:
        st.info("Status: Unknown")
        return
    status_upper = status.upper()
    if status_upper == "READY":
        st.success("🟢 **Status: READY** — Successfully processed and ingested.")
    elif status_upper == "NEEDS_REVIEW":
        st.warning("🟡 **Status: NEEDS REVIEW** — Extracted with lower confidence or missing fields.")
    elif status_upper == "FAILED":
        st.error("🔴 **Status: FAILED** — Could not extract structured data.")
    else:
        st.info(f"ℹ️ **Status: {status}**")


def render_upload_center() -> None:
    """Render the document upload form, real-time extraction results, and document library."""
    if not st.session_state.get("access_token"):
        st.warning("Please log in to access the Upload Center.")
        st.switch_page("pages/1_Login.py")
        return

    st.title("📂 Document Upload Center")
    st.markdown(
        "Upload medical records, prescriptions, and lab reports (PDF or images). "
        "Our AI will extract structured clinical data and synchronize it with your timeline and vector index."
    )

    with st.form("upload_form", clear_on_submit=False):
        st.subheader("Upload New Document")
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Select Medical File (.jpg, .jpeg, .png, .pdf)",
                type=["jpg", "jpeg", "png", "pdf"],
                help="Maximum file size: 15 MB",
            )
        with col2:
            selected_doc_type = st.selectbox(
                "Document Type",
                options=DOCUMENT_TYPES,
                format_func=lambda x: x.replace("_", " ").title(),
            )

        submit_btn = st.form_submit_button("🚀 Upload & Process Document", type="primary", use_container_width=True)

        if submit_btn:
            if not uploaded_file:
                st.error("Please select a file to upload.")
                st.toast("⚠️ Please select a file to upload.")
            else:
                try:
                    with st.spinner("Uploading document to storage..."):
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                        data = {"document_type": selected_doc_type}
                        res_upload = api_client.post("/documents/upload", data=data, files=files, auth=True)

                    doc_data = res_upload.get("data", {})
                    doc_id = doc_data.get("document_id")
                    if not doc_id:
                        st.error("Upload succeeded but did not return a valid document ID.")
                        return

                    st.toast("✅ File uploaded! Starting AI extraction...")

                    with st.spinner("Processing document — extracting text and analyzing..."):
                        res_process = api_client.post(f"/documents/{doc_id}/process", auth=True)

                    proc_data = res_process.get("data", {})
                    st.toast("🎉 Document processing completed!")

                    st.divider()
                    st.subheader("🎯 Extraction Results")
                    render_status_badge(proc_data.get("status"))

                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        conf = proc_data.get("ocr_confidence")
                        conf_str = f"{(conf * 100):.1f}%" if isinstance(conf, (int, float)) else "N/A"
                        st.metric("OCR Confidence", conf_str)
                    with m_col2:
                        st.metric("Prescriptions Found", str(proc_data.get("prescriptions_created", 0)))
                    with m_col3:
                        st.metric("Lab Results Found", str(proc_data.get("lab_results_created", 0)))

                    with st.expander("📄 Extracted Clinical Data JSON", expanded=True):
                        st.json(proc_data.get("extraction_json", {}))

                except Exception as exc:
                    st.toast(f"❌ Processing failed: {exc}")
                    st.error(f"Error processing document: {exc}")

    st.divider()
    st.subheader("📚 Document Library")

    try:
        limit = 10
        offset = st.session_state.get("doc_offset", 0)
        res_list = api_client.get("/documents", params={"limit": limit, "offset": offset}, auth=True)
        docs: list[dict[str, Any]] = res_list.get("data") or []

        if not docs and offset == 0:
            st.info("No documents uploaded yet.")
        else:
            for doc in docs:
                doc_id = str(doc.get("document_id", ""))
                doc_type_str = str(doc.get("document_type", "Unknown")).replace("_", " ").title()
                status_str = str(doc.get("status", "UNKNOWN"))
                uploaded_at = str(doc.get("uploaded_at", ""))[:19].replace("T", " ")

                with st.container(border=True):
                    row_col1, row_col2, row_col3 = st.columns([3, 2, 2])
                    with row_col1:
                        st.markdown(f"**{doc_type_str}** `({doc_id[:8]}...)`")
                        st.caption(f"Uploaded: {uploaded_at}")
                    with row_col2:
                        st.markdown(f"**Status**: `{status_str}`")
                        conf = doc.get("ocr_confidence")
                        if isinstance(conf, (int, float)):
                            st.caption(f"Confidence: {(conf * 100):.1f}%")
                    with row_col3:
                        confirm_key = f"confirm_del_{doc_id}"
                        if not st.session_state.get(confirm_key):
                            if st.button("🗑️ Delete", key=f"del_btn_{doc_id}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            st.warning("Confirm delete?")
                            del_col_a, del_col_b = st.columns(2)
                            with del_col_a:
                                if st.button("⚠️ Confirm", key=f"conf_btn_{doc_id}", type="primary", use_container_width=True):
                                    try:
                                        api_client.delete(f"/documents/{doc_id}", auth=True)
                                        st.session_state[confirm_key] = False
                                        st.toast("✅ Document and derived records deleted.")
                                        st.rerun()
                                    except Exception as exc:
                                        st.error(f"Delete failed: {exc}")
                            with del_col_b:
                                if st.button("❌ Cancel", key=f"canc_btn_{doc_id}", use_container_width=True):
                                    st.session_state[confirm_key] = False
                                    st.rerun()

                    with st.expander("🔍 View Extraction JSON"):
                        st.json(doc.get("extraction_json", {}))

            col_prev, col_next = st.columns(2)
            with col_prev:
                if offset > 0:
                    if st.button("⬅️ Previous Page", key="doc_prev"):
                        st.session_state["doc_offset"] = max(0, offset - limit)
                        st.rerun()
            with col_next:
                if len(docs) == limit:
                    if st.button("Load More Documents ➡️", key="doc_next"):
                        st.session_state["doc_offset"] = offset + limit
                        st.rerun()

    except Exception as exc:
        st.error(f"Failed to load document library: {exc}")


if __name__ == "__main__":
    render_upload_center()
