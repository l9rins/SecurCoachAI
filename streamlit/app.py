"""
app.py — SecurCoach AI Streamlit dashboard.
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
import time
import html as html_lib
import streamlit as st

# ── Validate config first ─────────────────────────────────────────────────────
import config
try:
    config.validate()
except RuntimeError as _cfg_err:
    st.set_page_config(page_title="SecurCoach AI", page_icon="🛡️", layout="wide")
    st.error(str(_cfg_err))
    st.stop()

import auth
import db
import chat

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecurCoach AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:       #1a1d23;
    --surface:  #22262e;
    --elevated: #2a2f3a;
    --border:   rgba(223,208,184,.1);
    --accent:   #c9a96e;
    --accent2:  #7eb8b0;
    --text1:    #e8dfd0;
    --text2:    rgba(232,223,208,.65);
    --text3:    rgba(232,223,208,.35);
    --danger:   #e07070;
    --radius:   10px;
}

html, body, .stApp { background: var(--bg) !important; color: var(--text1) !important; font-family: 'Inter', sans-serif !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text1) !important; }

/* ── Chat messages ── */
.msg-user, .msg-ai {
    padding: 14px 18px;
    border-radius: var(--radius);
    margin-bottom: 12px;
    font-size: .92rem;
    line-height: 1.7;
    position: relative;
}
.msg-user {
    background: var(--elevated);
    border-left: 3px solid var(--accent);
    margin-left: 2rem;
}
.msg-ai {
    background: rgba(126,184,176,.06);
    border-left: 3px solid var(--accent2);
    margin-right: 2rem;
}
.msg-meta {
    font-size: .73rem;
    color: var(--text3);
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}
code { font-family: 'JetBrains Mono', monospace !important; font-size: .85em !important; }
pre  { background: var(--bg) !important; border: 1px solid var(--border) !important;
       border-radius: 6px !important; padding: 12px !important; overflow-x: auto !important; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input,
div[data-testid="stChatInput"] textarea {
    background: var(--elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text1) !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(201,169,110,.15) !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text2) !important;
    border-radius: 6px !important;
    font-size: .82rem !important;
    transition: all .15s !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── Selectbox ── */
div[data-testid="stSelectbox"] > div > div {
    background: var(--elevated) !important;
    border: 1px solid var(--border) !important;
    color: var(--text1) !important;
    border-radius: var(--radius) !important;
}

/* ── Domain chips ── */
.domain-chip {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: .75rem;
    border: 1px solid var(--accent);
    color: var(--accent);
    background: rgba(201,169,110,.08);
    font-family: 'JetBrains Mono', monospace;
}

/* ── Error banner ── */
.err-banner {
    background: rgba(224,112,112,.12);
    border: 1px solid rgba(224,112,112,.4);
    border-radius: 8px;
    padding: 10px 14px;
    color: var(--danger);
    font-size: .84rem;
    margin-bottom: 12px;
}

/* ── Header ── */
h1 { font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
     background: linear-gradient(90deg, var(--accent), var(--accent2));
     -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; }
h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 700 !important; color: var(--text1) !important; }

/* ── Rate limit ── */
.rate-msg { font-size:.8rem; color: var(--text3); margin-top:4px; font-style: italic; }

/* ── Export button special ── */
.stDownloadButton > button {
    background: rgba(126,184,176,.1) !important;
    border-color: var(--accent2) !important;
    color: var(--accent2) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: .75rem 0 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────

def _init_state() -> None:
    auth.init_session()
    auth.apply_query_auth()

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("total_interactions", 0)
    st.session_state.setdefault("session_start", datetime.now())
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("is_generating", False)
    st.session_state.setdefault("selected_domain", chat.DOMAINS[0])
    st.session_state.setdefault("last_msg_time", 0.0)
    st.session_state.setdefault("conv_title_set", False)
    st.session_state.setdefault("current_conv_title", "conversation")

    user_id = auth.get_user_email()
    if st.session_state.is_authenticated and user_id:
        if not st.session_state.get("conversations_loaded"):
            _refresh_conversations()
            st.session_state.conversations_loaded = True

        if not st.session_state.current_conversation_id:
            if st.session_state.conversation_summaries:
                _select_conversation(
                    st.session_state.conversation_summaries[0]["conversation_id"]
                )
            else:
                _new_conversation()
        elif not st.session_state.conversation_loaded:
            st.session_state.messages = db.load_messages_for_conversation(
                user_id, st.session_state.current_conversation_id
            )
            st.session_state.conversation_loaded = True


def _refresh_conversations(force: bool = False) -> None:
    if force or not st.session_state.get("conversations_loaded"):
        user_id = auth.get_user_email()
        if user_id:
            st.session_state.conversation_summaries = db.load_conversation_summaries(user_id)
            st.session_state.conversations_loaded = True


def _new_conversation() -> None:
    st.session_state.current_conversation_id = db.new_conversation_id()
    st.session_state.messages = []
    st.session_state.conversation_loaded = True
    st.session_state.conv_title_set = False
    st.session_state.current_conv_title = "conversation"


def _select_conversation(cid: str) -> None:
    user_id = auth.get_user_email()
    st.session_state.current_conversation_id = cid
    st.session_state.messages = db.load_messages_for_conversation(user_id, cid)
    st.session_state.conversation_loaded = True
    st.session_state.conv_title_set = True
    st.session_state.current_conv_title = next(
        (s["title"] for s in st.session_state.get("conversation_summaries", [])
         if s["conversation_id"] == cid), "conversation"
    )


def _rate_limited() -> bool:
    now = time.time()
    last = st.session_state.get("last_msg_time", 0.0)
    if now - last < 2.0:
        return True
    st.session_state.last_msg_time = now
    return False


def _group_conversations(summaries: list[dict]) -> dict[str, list[dict]]:
    today     = date.today()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)
    groups    = {"Today": [], "Yesterday": [], "This week": [], "Older": []}
    for s in summaries:
        try:
            d = date.fromisoformat(s["created_at"][:10])
        except Exception:
            d = date.min
        if d == today:       groups["Today"].append(s)
        elif d == yesterday: groups["Yesterday"].append(s)
        elif d >= week_ago:  groups["This week"].append(s)
        else:                groups["Older"].append(s)
    return {k: v for k, v in groups.items() if v}


# ── Rendering helpers ─────────────────────────────────────────────────────────

def _render_message(msg: dict, container: st.delta_generator.DeltaGenerator | None = None) -> None:
    role  = msg["role"]
    ts    = msg.get("timestamp", "")
    label = "You" if role == "user" else "🛡️ SecurCoach"
    cls   = "msg-user" if role == "user" else "msg-ai"
    safe_ts = html_lib.escape(ts)
    
    target = container or st
    # Render the header
    target.markdown(
        f'<div class="{cls}"><div class="msg-meta">{label} · {safe_ts}</div></div>',
        unsafe_allow_html=True,
    )
    # Let Streamlit render markdown properly inside a container
    with target.container():
        target.markdown(msg["content"])

def _export_markdown() -> str:
    domain = st.session_state.get("selected_domain", "")
    lines = [f"# SecurCoach AI — {domain} conversation\n"]
    for msg in st.session_state.messages:
        role  = "**You**" if msg["role"] == "user" else "**SecurCoach**"
        ts    = msg.get("timestamp", "")
        lines.append(f"{role} _{ts}_\n")
        lines.append(msg["content"])
        lines.append("\n---")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

_init_state()

if not auth.require_auth():
    st.stop()

user_email = auth.get_user_email()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ SecurCoach AI")
    st.markdown(f"<small style='color:var(--text3)'>{html_lib.escape(user_email)}</small>", unsafe_allow_html=True)
    st.divider()

    # Domain selector
    st.markdown("**Domain**")
    new_domain = st.selectbox(
        "Domain",
        chat.DOMAINS,
        index=chat.DOMAINS.index(st.session_state.selected_domain),
        label_visibility="collapsed",
    )
    if new_domain != st.session_state.selected_domain:
        if st.session_state.messages:
            st.warning(
                f"Switching domain to **{new_domain}** will change the AI's context. "
                "Start a new conversation for the best results."
            )
        st.session_state.selected_domain = new_domain

    st.divider()

    # New conversation
    if st.button("＋  New conversation", use_container_width=True):
        _new_conversation()
        _refresh_conversations(force=True)
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Conversation list
    summaries = st.session_state.get("conversation_summaries", [])
    current_cid = st.session_state.current_conversation_id

    if summaries:
        grouped = _group_conversations(summaries)
        for group_name, items in grouped.items():
            st.markdown(f"<small style='color:var(--text3)'>{group_name}</small>", unsafe_allow_html=True)
            for s in items[:15]:  # show up to 15 per group
                cid   = s["conversation_id"]
                title = s["title"]
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(title, key=f"conv_{cid}", use_container_width=True):
                        _select_conversation(cid)
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{cid}"):
                        db.delete_conversation(user_email, cid)
                        if cid == current_cid:
                            _new_conversation()
                        _refresh_conversations(force=True)
                        st.rerun()
    else:
        st.markdown("<small style='color:var(--text3)'>No conversations yet.</small>", unsafe_allow_html=True)

    st.divider()

    # Stats
    elapsed = (datetime.now() - st.session_state.session_start)
    mins    = int(elapsed.total_seconds() // 60)
    st.markdown(
        f"<small style='color:var(--text3)'>Session: {mins}m &nbsp;|&nbsp; "
        f"Sent: {st.session_state.total_interactions}</small>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Export
    if st.session_state.messages:
        title_slug = st.session_state.get("current_conv_title", "conversation")
        title_slug = "".join(c if c.isalnum() else "_" for c in title_slug)[:30]
        filename   = f"securcoach_{title_slug}_{datetime.now().strftime('%Y%m%d')}.md"
        st.download_button(
            "⬇ Export conversation",
            data=_export_markdown(),
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
        )

# ── Main area ─────────────────────────────────────────────────────────────────
header_col, chip_col = st.columns([6, 2])
with header_col:
    st.markdown("# SecurCoach AI")
with chip_col:
    st.markdown(
        f"<div style='padding-top:18px;text-align:right'>"
        f"<span class='domain-chip'>{html_lib.escape(st.session_state.selected_domain)}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

# DB error banner
db_err = db.get_error()
if db_err:
    st.markdown(f'<div class="err-banner">⚠️ Database error: {html_lib.escape(db_err)}</div>', unsafe_allow_html=True)
    db.clear_error()

st.divider()

# ── Suggested questions (when chat is empty) ──────────────────────────────────
if not st.session_state.messages:
    suggestions = chat.get_suggestions(st.session_state.selected_domain)
    if suggestions:
        st.markdown(
            f"<p style='color:var(--text2);margin-bottom:12px'>"
            f"Getting started with <strong style='color:var(--accent)'>"
            f"{st.session_state.selected_domain}</strong>:</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(suggestions))
        for col, q in zip(cols, suggestions):
            with col:
                if st.button(q, use_container_width=True, key=f"sug_{q[:20]}"):
                    st.session_state.pending_prompt = q
                    st.rerun()

    st.markdown(
        "<div style='text-align:center;padding:3rem 0 1rem;"
        "color:var(--text3);font-size:.9rem'>"
        "Ask anything about cybersecurity — or pick a suggestion above.</div>",
        unsafe_allow_html=True,
    )

# ── Message history ───────────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        _render_message(msg)

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    placeholder=f"Ask about {st.session_state.selected_domain.lower()}...",
    disabled=st.session_state.is_generating,
)

# Accept either typed input or suggestion click
prompt: str | None = user_input or st.session_state.pop("pending_prompt", None)

if prompt:
    if _rate_limited():
        st.warning("Please wait a moment before sending another message.")
        st.stop()

    now_ts = datetime.now().strftime("%H:%M")

    # Add user message
    user_msg = {"role": "user", "content": prompt, "timestamp": now_ts}
    st.session_state.messages.append(user_msg)
    db.save_message(
        user_email,
        st.session_state.current_conversation_id,
        "user",
        prompt,
    )
    st.session_state.total_interactions += 1

    # Re-render history including the new user message
    with chat_container:
        _render_message(user_msg)

    # ── Stream AI response ────────────────────────────────────────────────────
    st.session_state.is_generating = True
    ai_placeholder = st.empty()
    full_response   = ""

    try:
        stream = chat.stream_response(st.session_state.messages)
        buffer = ""
        for chunk in stream:
            buffer += chunk
            full_response = buffer
            # Use a container to render header (HTML) and body (Markdown) separately
            # so that bold/code blocks in the buffer are rendered by Streamlit.
            with ai_placeholder.container():
                st.markdown(
                    f'<div class="msg-ai"><div class="msg-meta">🛡️ SecurCoach · {now_ts}</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"{buffer}▌")

        # Final render without cursor
        if not full_response.strip():
            full_response = "⚠️ No response received. Gemini may be rate-limited — please try again."
            ai_placeholder.markdown(
                f'<div class="err-banner">{full_response}</div>',
                unsafe_allow_html=True,
            )
        else:
            ai_placeholder.markdown(
                f'<div class="msg-ai">'
                f'<div class="msg-meta">🛡️ SecurCoach · {now_ts}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _render_message({"role": "assistant", "content": full_response, "timestamp": now_ts}, container=ai_placeholder)

    except Exception as exc:
        full_response = f"⚠️ Error: {exc}"
        ai_placeholder.markdown(
            f'<div class="err-banner">{full_response}</div>',
            unsafe_allow_html=True,
        )
    finally:
        st.session_state.is_generating = False

    if full_response and not full_response.startswith("⚠️"):
        # Save AI response
        ai_msg = {"role": "assistant", "content": full_response, "timestamp": now_ts}
        st.session_state.messages.append(ai_msg)
        db.save_message(
            user_email,
            st.session_state.current_conversation_id,
            "assistant",
            full_response,
        )

        # Generate AI title on first exchange
        if not st.session_state.conv_title_set and len(st.session_state.messages) <= 2:
            title = chat.generate_title(prompt)
            db.update_conversation_title(
                user_email, st.session_state.current_conversation_id, title
            )
            st.session_state.conv_title_set = True
            st.session_state.current_conv_title = title
            _refresh_conversations(force=True)

    st.rerun()
