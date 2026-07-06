"""Login page for MediMind AI."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(page_title="Login - MediMind AI", page_icon="🔑")

# Ensure session state variables exist
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None


def render_login_page() -> None:
    """Render the login form and handle authentication submission."""
    st.title("🔑 Account Login")

    if st.session_state.get("access_token"):
        st.info(f"You are already logged in as **{st.session_state.get('user_name', 'Patient')}**.")
        if st.button("⬅️ Return to Main Portal", type="primary"):
            st.switch_page("app.py")
        return

    st.markdown("Please enter your email and password to access your MediMind AI portal.")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email Address", placeholder="patient@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                st.toast("⚠️ Please enter both email and password.")
                return
            if "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
                st.toast("⚠️ Please enter a valid email address.")
                return

            try:
                with st.spinner("Authenticating..."):
                    res = api_client.post(
                        "/login",
                        json={"email": email.strip().lower(), "password": password},
                        auth=False,
                    )

                token_data = res.get("data", {})
                token = token_data.get("access_token")
                if not token:
                    st.error("Login failed: Did not receive an access token from server.")
                    st.toast("❌ Login failed: No token received.")
                    return

                st.session_state["access_token"] = token

                # Fetch user profile to display name in sidebar
                try:
                    user_res = api_client.get("/me", auth=True)
                    user_data = user_res.get("data", {})
                    st.session_state["user_name"] = user_data.get("full_name") or email
                except Exception:
                    st.session_state["user_name"] = email

                st.toast(f"🎉 Welcome back, {st.session_state['user_name']}!")
                st.success("Login successful! Redirecting to portal...")
                st.switch_page("app.py")

            except Exception as exc:
                st.toast(f"❌ Login failed: {exc}")
                st.error(f"Login failed: {exc}")

    st.divider()
    st.markdown("Don't have an account yet?")
    st.page_link("pages/2_Register.py", label="📝 Create a New Account", icon="👉")


if __name__ == "__main__":
    render_login_page()
