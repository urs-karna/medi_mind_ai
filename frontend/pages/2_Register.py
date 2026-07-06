"""Registration page for MediMind AI."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(page_title="Register - MediMind AI", page_icon="📝")

# Ensure session state variables exist
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None


def render_register_page() -> None:
    """Render the user and patient profile registration form."""
    st.title("📝 Create a New Account")

    if st.session_state.get("access_token"):
        st.info("You are currently logged in. Logout first if you wish to register a new account.")
        if st.button("⬅️ Return to Main Portal", type="primary"):
            st.switch_page("app.py")
        return

    st.markdown("Fill out the form below to register your account and set up your medical profile.")

    with st.form("register_form", clear_on_submit=False):
        st.subheader("Account Credentials")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Jane Doe")
        with col2:
            email = st.text_input("Email Address *", placeholder="jane.doe@example.com")

        password = st.text_input("Password (min. 8 characters) *", type="password", placeholder="••••••••")
        password_confirm = st.text_input("Confirm Password *", type="password", placeholder="••••••••")

        st.subheader("Patient Profile Details (Optional)")
        col3, col4 = st.columns(2)
        with col3:
            gender = st.selectbox("Gender", options=["", "Female", "Male", "Other", "Prefer not to say"], index=0)
            date_of_birth = st.date_input(
                "Date of Birth",
                value=None,
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today(),
            )
        with col4:
            height_cm = st.number_input("Height (cm)", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=0.0, step=0.5)

        submitted = st.form_submit_button("Register Account", type="primary", use_container_width=True)

        if submitted:
            if not full_name or not email or not password:
                st.error("Please fill in all required fields marked with *.")
                st.toast("⚠️ Please fill in all required fields marked with *.")
                return
            if "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
                st.toast("⚠️ Please enter a valid email address.")
                return
            if len(password) < 8:
                st.error("Password must be at least 8 characters long.")
                st.toast("⚠️ Password must be at least 8 characters long.")
                return
            if password != password_confirm:
                st.error("Passwords do not match.")
                st.toast("⚠️ Passwords do not match.")
                return

            payload: dict[str, object] = {
                "full_name": full_name.strip(),
                "email": email.strip().lower(),
                "password": password,
            }
            if gender:
                payload["gender"] = gender
            if date_of_birth:
                payload["date_of_birth"] = date_of_birth.isoformat()
            if height_cm > 0:
                payload["height_cm"] = float(height_cm)
            if weight_kg > 0:
                payload["weight_kg"] = float(weight_kg)

            try:
                with st.spinner("Creating account..."):
                    res = api_client.post("/register", json=payload, auth=False)

                st.toast("🎉 Account created successfully! Please log in.")
                st.success("Account created successfully! Please log in with your new credentials.")
                st.page_link("pages/1_Login.py", label="🔑 Go to Login Page", icon="👉")

            except Exception as exc:
                st.toast(f"❌ Registration failed: {exc}")
                st.error(f"Registration failed: {exc}")


if __name__ == "__main__":
    render_register_page()
