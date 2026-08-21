"""Timeline page for MediMind AI."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.utils import api_client

st.set_page_config(page_title="Timeline - MediMind AI", page_icon="⏳", layout="wide")

# Ensure session state variables exist
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "tm_offset" not in st.session_state:
    st.session_state["tm_offset"] = 0


def _format_month_header(date_str: str) -> str:
    """Format a YYYY-MM-DD date string into a readable month header (e.g., 'July 2026')."""
    if not date_str or len(date_str) < 7:
        return "Unknown Date"
    try:
        dt = datetime.strptime(date_str[:7], "%Y-%m")
        return dt.strftime("%B %Y")
    except Exception:
        return date_str[:7]


def _get_event_badge(event_type: str | None) -> str:
    """Return a styled badge string and icon for a timeline event type."""
    if not event_type:
        return "📌 Event"
    etype = event_type.lower()
    if "prescription" in etype or "medication" in etype:
        return "💊 Prescription"
    elif "lab" in etype or "test" in etype:
        return "🧪 Lab Test"
    elif "doctor" in etype or "visit" in etype:
        return "🩺 Doctor Visit"
    elif "condition" in etype or "diagnosis" in etype:
        return "❤️ Diagnosis"
    return f"📌 {event_type.replace('_', ' ').title()}"


def render_timeline() -> None:
    """Render the chronological medical timeline grouped by month."""
    if not st.session_state.get("access_token"):
        st.warning("Please log in to access your Timeline.")
        st.switch_page("pages/1_Login.py")
        return

    st.title("⏳ Medical Timeline")
    st.markdown("A reverse-chronological view of your health events, doctor visits, prescriptions, and lab tests.")

    limit = 20
    offset = st.session_state.get("tm_offset", 0)

    try:
        res = api_client.get("/timeline", params={"limit": limit, "offset": offset}, auth=True)
        events: list[dict[str, Any]] = res.get("data") or []

        if not events and offset == 0:
            st.info("No timeline events recorded yet.")
        else:
            current_month: str | None = None
            for event in events:
                date_str = str(event.get("event_date") or "Unknown Date")
                month_str = _format_month_header(date_str)

                if month_str != current_month:
                    st.subheader(f"📅 {month_str}")
                    current_month = month_str

                badge_str = _get_event_badge(event.get("event_type"))
                summary = event.get("summary") or "No summary provided."

                with st.container(border=True):
                    col_date, col_summary = st.columns([1, 4])
                    with col_date:
                        st.markdown(f"**`{date_str}`**")
                        st.caption(badge_str)
                    with col_summary:
                        st.markdown(f"**{summary}**")

            col_prev, col_next = st.columns(2)
            with col_prev:
                if offset > 0:
                    if st.button("⬅️ Previous Events", key="tm_prev"):
                        st.session_state["tm_offset"] = max(0, offset - limit)
                        st.rerun()
            with col_next:
                if len(events) == limit:
                    if st.button("Load More Events ➡️", key="tm_next"):
                        st.session_state["tm_offset"] = offset + limit
                        st.rerun()

    except Exception as exc:
        st.error(f"Failed to fetch timeline events: {exc}")


if __name__ == "__main__":
    render_timeline()
