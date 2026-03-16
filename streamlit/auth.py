"""
auth.py — JWT verification via PyJWT only. No insecure fallbacks.
"""
from __future__ import annotations
import streamlit as st

try:
    import jwt as pyjwt
    _HAS_PYJWT = True
except ImportError:
    _HAS_PYJWT = False

import config


def verify_jwt(token: str) -> str | None:
    """
    Verify a Supabase JWT and return the user's email, or None on failure.
    Requires PyJWT and SUPABASE_JWT_SECRET — fails closed (returns None) if
    either is unavailable.
    """
    if not token:
        return None
    if not _HAS_PYJWT:
        st.error("PyJWT is not installed. Run: pip install PyJWT")
        return None
    secret = config.supabase_jwt_secret()
    if not secret:
        st.error("SUPABASE_JWT_SECRET is not configured.")
        return None
    try:
        payload = pyjwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        email = payload.get("email", "")
        return email.lower().strip() if email else None
    except pyjwt.ExpiredSignatureError:
        st.warning("Session expired. Please log in again.")
        return None
    except pyjwt.InvalidTokenError:
        return None


def init_session() -> None:
    st.session_state.setdefault("is_authenticated", False)
    st.session_state.setdefault("auth_user_email", "")
    st.session_state.setdefault("conversation_loaded", False)
    st.session_state.setdefault("current_conversation_id", "")
    st.session_state.setdefault("conversation_summaries", [])


def apply_query_auth() -> None:
    """
    Authenticate via ?token=<jwt> in the URL.
    Only accepts a properly signed JWT — no plain-text email bypass.
    """
    token = st.query_params.get("token", "").strip()
    if not token:
        return
    email = verify_jwt(token)
    if email:
        st.session_state.is_authenticated = True
        st.session_state.auth_user_email = email
        st.session_state.conversation_loaded = False
        # Remove token from URL after consuming it
        try:
            st.query_params.clear()
        except Exception:
            pass


def get_user_email() -> str:
    return st.session_state.get("auth_user_email", "").strip().lower()


def require_auth() -> bool:
    """Returns True if authenticated, False otherwise (and shows login prompt)."""
    if not st.session_state.get("is_authenticated"):
        react_url = config.react_app_url()
        st.markdown(
            f"""
            <div style="text-align:center;padding:4rem 2rem;">
              <h2 style="color:#DFD0B8;">Access Denied</h2>
              <p style="color:#948979;">Please log in through the React frontend first.</p>
              <a href="{react_url}" target="_self"
                 style="display:inline-block;margin-top:1rem;padding:.75rem 2rem;
                        background:#948979;color:#222831;border-radius:8px;
                        font-weight:600;text-decoration:none;">
                Go to Login
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return False
    return True
