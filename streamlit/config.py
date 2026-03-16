"""
config.py — loads and validates all secrets at startup.
Raises a clear RuntimeError if any required key is missing.
"""
from __future__ import annotations
import os
import streamlit as st


_REQUIRED = [
    "GEMINI_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "SUPABASE_JWT_SECRET",
]


def _get(key: str, default: str = "") -> str:
    try:
        val = st.secrets[key]
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default) or default


def validate() -> None:
    missing = [k for k in _REQUIRED if not _get(k)]
    if missing:
        raise RuntimeError(
            f"Missing required secrets/env vars: {', '.join(missing)}\n"
            "Create .streamlit/secrets.toml — see README.md."
        )


# ── Public accessors ──────────────────────────────────────────────────────────

def gemini_api_key() -> str:
    return _get("GEMINI_API_KEY")

def supabase_url() -> str:
    return _get("SUPABASE_URL").rstrip("/")

def supabase_key() -> str:
    return _get("SUPABASE_KEY")

def supabase_jwt_secret() -> str:
    return _get("SUPABASE_JWT_SECRET")

def react_app_url() -> str:
    return _get("REACT_APP_URL", "http://localhost:3000")

def chat_history_table() -> str:
    return _get("SUPABASE_CHAT_HISTORY_TABLE", "chat_history")
