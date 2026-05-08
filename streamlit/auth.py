"""
auth.py — JWT verification via PyJWT only. No insecure fallbacks.
"""
from __future__ import annotations
import html
import time
import logging

logger = logging.getLogger(__name__)
import streamlit as st

try:
    import jwt as pyjwt
    _HAS_PYJWT = True
except ImportError:
    _HAS_PYJWT = False

import config


def verify_jwt(token: str) -> str | None:
    if not token:
        return None
    if not _HAS_PYJWT:
        st.error("PyJWT is not installed. Run: pip install PyJWT")
        return None
    try:
        # Decode header to check algorithm without verification
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "HS256":
            secret = config.supabase_jwt_secret()
            if not secret:
                st.error("SUPABASE_JWT_SECRET is not configured.")
                return None
            payload = pyjwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            # ES256 — fetch Supabase JWKS public key
            import urllib.request, json
            supabase_url = config.supabase_url()
            jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
            with urllib.request.urlopen(jwks_url) as r:
                jwks = json.loads(r.read())
            from jwt.algorithms import ECAlgorithm
            kid = header.get("kid")
            key_data = next(
                (k for k in jwks["keys"] if k.get("kid") == kid),
                jwks["keys"][0]
            )
            public_key = ECAlgorithm.from_jwk(json.dumps(key_data))
            payload = pyjwt.decode(
                token,
                public_key,
                algorithms=["ES256"],
                audience="authenticated",
            )

        email = payload.get("email", "")
        # Store expiry for periodic re-validation
        exp = payload.get("exp")
        if exp:
            st.session_state["jwt_exp"] = exp
        return email.lower().strip() if email else None

    except pyjwt.ExpiredSignatureError:
        st.warning("Session expired. Please log in again.")
        return None
    except pyjwt.InvalidTokenError:
        return None
    except Exception as e:
        st.error(f"Auth error: {e}")
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
    
    Flow:
    1. Check if token in URL
    2. If yes and not yet processed: verify JWT → store in session → remove token → trigger rerun
    3. If yes and already processed: do nothing (rerun will skip this)
    """
    params = st.query_params
    token = params.get("token", "").strip()
    
    if not token:
        return
    
    # If we've already processed this token in a previous run, skip
    if st.session_state.get("processed_token") == token:
        logger.debug("Token already processed in previous run, skipping.")
        return
    
    logger.info(f"Token received in URL")
    
    # Verify the JWT
    email = verify_jwt(token)
    if not email:
        logger.warning("Token verification failed")
        return
    
    logger.info(f"Token verified for email: {email}")
    
    # Store authentication state
    st.session_state.is_authenticated = True
    st.session_state.auth_user_email = email
    st.session_state.conversation_loaded = False
    st.session_state["processed_token"] = token
    
    # Remove token from URL to prevent re-processing on rerun
    try:
        del st.query_params["token"]
        logger.info("Token removed from URL")
    except Exception as e:
        logger.error(f"Failed to remove token from URL: {e}")
        # If removal fails, at least we have processed_token set to prevent loops
        return
    
    # Trigger rerun to show authenticated app without token in URL
    logger.info("Triggering rerun to show authenticated app")
    st.rerun()


def get_user_email() -> str:
    return st.session_state.get("auth_user_email", "").strip().lower()


def _is_session_expired() -> bool:
    """Check if the JWT has expired since initial authentication."""
    exp = st.session_state.get("jwt_exp")
    if exp and time.time() > exp:
        return True
    return False


def require_auth() -> bool:
    """Returns True if authenticated, False otherwise (and shows login prompt)."""
    if not st.session_state.get("is_authenticated"):
        react_url = config.react_app_url()
        safe_url = html.escape(react_url)
        st.markdown(
            f"""
            <div style="text-align:center;padding:4rem 2rem;">
              <h2 style="color:#DFD0B8;">Access Denied</h2>
              <p style="color:#948979;">Please log in through the React frontend first.</p>
              <a href="{safe_url}" target="_self"
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

    # Periodic JWT expiry re-check
    if _is_session_expired():
        st.session_state.is_authenticated = False
        st.session_state.auth_user_email = ""
        react_url = config.react_app_url()
        safe_url = html.escape(react_url)
        st.warning("Your session has expired. Please log in again.")
        st.markdown(
            f'<a href="{safe_url}" target="_self" '
            f'style="display:inline-block;margin-top:.5rem;padding:.6rem 1.5rem;'
            f'background:#948979;color:#222831;border-radius:8px;'
            f'font-weight:600;text-decoration:none;">Go to Login</a>',
            unsafe_allow_html=True,
        )
        return False

    return True
