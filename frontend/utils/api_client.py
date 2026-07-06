"""HTTP API client wrapper for communicating with the MediMind AI backend."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.config import BACKEND_BASE_URL


class APIException(Exception):
    """Exception raised when an API request fails with a non-2xx status code."""
    pass


def _request(method: str, path: str, auth: bool = True, **kwargs: Any) -> Any:
    """Execute an HTTP request against the backend API and handle authentication and errors."""
    url = f"{BACKEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = kwargs.pop("headers", {}) or {}

    if auth:
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(method, url, headers=headers, **kwargs)
    except requests.RequestException as exc:
        raise APIException(f"Network error communicating with server: {exc}") from exc

    if not response.ok:
        if response.status_code == 401 and auth:
            st.session_state["access_token"] = None
            st.session_state["user_name"] = None
            try:
                st.switch_page("pages/1_Login.py")
            except Exception:
                pass
            raise APIException("Session expired or unauthorized. Please log in again.")

        error_msg = f"HTTP {response.status_code} Error"
        try:
            payload = response.json()
            if isinstance(payload, dict):
                if "message" in payload and payload["message"]:
                    error_msg = str(payload["message"])
                    if payload.get("data") and isinstance(payload["data"], dict) and "errors" in payload["data"]:
                        val_errors = payload["data"]["errors"]
                        val_msgs = [
                            f"{'.'.join(str(loc) for loc in err.get('loc', []))}: {err.get('msg', '')}"
                            for err in val_errors if isinstance(err, dict)
                        ]
                        if val_msgs:
                            error_msg += f" ({', '.join(val_msgs)})"
                elif "detail" in payload:
                    error_msg = str(payload["detail"])
                elif "error" in payload:
                    error_msg = str(payload["error"])
        except Exception:
            error_msg = response.text or error_msg

        raise APIException(error_msg)

    try:
        return response.json()
    except Exception:
        return response.text


def get(path: str, params: dict[str, Any] | None = None, auth: bool = True, **kwargs: Any) -> Any:
    """Send an HTTP GET request to the backend API."""
    return _request("GET", path, auth=auth, params=params, **kwargs)


def post(path: str, json: dict[str, Any] | None = None, data: dict[str, Any] | None = None, auth: bool = True, **kwargs: Any) -> Any:
    """Send an HTTP POST request to the backend API."""
    return _request("POST", path, auth=auth, json=json, data=data, **kwargs)


def put(path: str, json: dict[str, Any] | None = None, data: dict[str, Any] | None = None, auth: bool = True, **kwargs: Any) -> Any:
    """Send an HTTP PUT request to the backend API."""
    return _request("PUT", path, auth=auth, json=json, data=data, **kwargs)


def delete(path: str, params: dict[str, Any] | None = None, auth: bool = True, **kwargs: Any) -> Any:
    """Send an HTTP DELETE request to the backend API."""
    return _request("DELETE", path, auth=auth, params=params, **kwargs)
