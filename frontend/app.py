"""Streamlit frontend entry point and authentication gate for MediMind AI."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(
    page_title="MediMind AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# TASK 4: Establish Session State Convention
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None


def main() -> None:
    """Render the main landing page or welcome portal based on authentication state."""
    st.title("🩺 MediMind AI Portal")

    # Check authentication state
    if not st.session_state.get("access_token"):
        st.markdown(
            """
            ### Welcome to MediMind AI
            Your intelligent, grounded medical assistant and healthcare management platform.

            Please log in to access your medical records, chat assistant, and profile, or create a new account if you are visiting for the first time.
            """
        )
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            if st.button("🔑 Login", type="primary", use_container_width=True):
                st.switch_page("pages/1_Login.py")
        with col2:
            if st.button("📝 Register", use_container_width=True):
                st.switch_page("pages/2_Register.py")
    else:
        user_name = st.session_state.get("user_name") or "Patient"

        # Render Sidebar
        with st.sidebar:
            st.markdown(f"### 👋 Welcome, **{user_name}**!")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                try:
                    api_client.post("/logout", auth=True)
                except Exception:
                    pass
                st.session_state["access_token"] = None
                st.session_state["user_name"] = None
                st.success("You have been logged out.")
                st.rerun()

        # Custom CSS for modern card aesthetics
        st.markdown(
            """
            <style>
            .portal-card {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.success(f"🎉 Successfully logged in as **{user_name}**.")
        st.markdown("### 📊 Your Medical Overview")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Medical Records", value="Active", delta="Ready for Upload")
        with col2:
            st.metric(label="Health Timeline", value="Synchronized", delta="Real-time")
        with col3:
            st.metric(label="AI Assistant", value="Grounded", delta="Phase 5 RAG")
        with col4:
            st.metric(label="Safety Gate", value="Protected", delta="100% Deterministic")

        st.divider()
        st.subheader("🚀 Portal Modules")

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            with st.container(border=True):
                st.markdown("#### 📂 Upload Center & Records")
                st.write("Upload PDF medical records, prescriptions, and lab reports. Documents are automatically parsed, embedded, and synchronized to Pinecone.")
                st.info("📌 **Coming in Phase 8, Part B**")

            with st.container(border=True):
                st.markdown("#### 💬 Grounded Chat Assistant")
                st.write("Ask questions about your health, medications, and lab reports. Powered by hybrid RAG retrieval and deterministic safety gates.")
                st.info("📌 **Coming in Phase 8, Part C**")

        with m_col2:
            with st.container(border=True):
                st.markdown("#### ⏳ Medical Timeline")
                st.write("Explore a chronological, unified timeline of your medical events, doctor visits, diagnoses, and treatments.")
                st.info("📌 **Coming in Phase 8, Part B**")

            with st.container(border=True):
                st.markdown("#### 👤 Patient Profile & Conditions")
                st.write("Manage your personal details, allergies, and chronic conditions with automatic Pinecone vector synchronization.")
                st.info("📌 **Coming in Phase 8, Part C**")


if __name__ == "__main__":
    main()
