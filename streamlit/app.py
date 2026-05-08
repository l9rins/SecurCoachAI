"""
app.py — SecurCoach AI Streamlit dashboard.
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
import time
import html as html_lib
import pathlib
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
import llm_engine
import quiz
import progress

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SecurCoach AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
_CSS_PATH = pathlib.Path(__file__).parent / "dashboard.css"
st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

def _init_state() -> None:
    auth.init_session()
    auth.apply_query_auth()

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("total_interactions", 0)
    st.session_state.setdefault("session_start", datetime.now())
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("is_generating", False)
    st.session_state.setdefault("selected_domain", llm_engine.DOMAINS[0])
    st.session_state.setdefault("selected_model", llm_engine.DEFAULT_MODEL)
    st.session_state.setdefault("lab_mode", False)
    st.session_state.setdefault("last_msg_time", 0.0)
    st.session_state.setdefault("conv_title_set", False)
    st.session_state.setdefault("current_conv_title", "conversation")
    st.session_state.setdefault("stop_generation", False)
    st.session_state.setdefault("search_query", "")
    st.session_state.setdefault("active_page", "💬 Chat")

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

def _clean_response(text: str) -> str:
    """Strip prompt artifacts and metadata, and augment headers with icons."""
    import re
    # Remove metadata lines like TITLE: ... or CATEGORY: ...
    text = re.sub(r'^(TITLE|CATEGORY|TOPIC|DOMAIN):\s*.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Replace markdown headers with styled headers and icons
    # ph-book-open for Answer, ph-test-tube for Example, ph-brain for Think About This
    text = re.sub(
        r'^## Answer', 
        r'<div class="response-header"><i class="ph ph-book-open"></i><span>Answer</span></div>', 
        text, flags=re.MULTILINE
    )
    text = re.sub(
        r'^## Example', 
        r'<div class="response-header"><i class="ph ph-test-tube"></i><span>Example</span></div>', 
        text, flags=re.MULTILINE
    )
    
    # Special case for "Think About This": Wrap in the think-block class
    think_match = re.search(r'^## Think About This\s*(.*)', text, flags=re.MULTILINE | re.DOTALL)
    if think_match:
        think_text = think_match.group(1).strip()
        # Remove the match from the main text
        text = text[:think_match.start()]
        text += (
            f'<div class="response-header" style="margin-top:12px;color:#4A7A9A">'
            f'<i class="ph ph-brain"></i><span>Think About This</span></div>'
            f'<div class="think-block">{think_text}</div>'
        )

    # Remove trailing newlines and whitespace
    return text.strip()

def _render_message(msg: dict, container: st.delta_generator.DeltaGenerator | None = None) -> None:
    role  = msg["role"]
    ts    = msg.get("timestamp", "")
    raw_content = msg["content"]

    # Use a sub-container if a target container is provided, so multiple elements don't overwrite each other.
    target = container.container() if container else st

    if role == "user":
        # Always escape user content to avoid HTML injection
        target.markdown(
            f'<div class="msg-user"><div class="msg-user-bubble">{html_lib.escape(raw_content)}</div></div>',
            unsafe_allow_html=True,
        )
        return

    # AI message: render header, then render content while respecting code fences.
    header_html = (
        f'<div class="msg-meta">'
        f'<div class="avatar" style="width:20px;height:20px;border-radius:5px;background:#1A1508;border:0.5px solid rgba(193,148,60,0.4);display:flex;align-items:center;justify-content:center">'
        f'<i class="ph ph-shield" style="font-size:11px;color:#C1943C"></i></div>'
        f'<span class="name" style="color:var(--color-accent-gold);font-family:\'Space Grotesk\'">SecurCoach AI</span>'
        f'<span class="sep">·</span>'
        f'<span class="time">{html_lib.escape(ts)}</span>'
        f'</div>'
    )

    # Start the AI message container and header inside a native Streamlit block to prevent orphaned <div> tags
    with target.container(border=True):
        st.markdown(f'<div class="ai-msg-flag" style="display:none"></div>{header_html}', unsafe_allow_html=True)

        # Split raw content into alternating non-code and code blocks (```...```) so we can render each appropriately
        import re
        parts = re.split(r'(```[\s\S]*?```)', raw_content)
        for part in parts:
            if not part:
                continue
            if part.startswith('```'):
                # Extract optional language and code body
                m = re.match(r'```(\w+)?\n([\s\S]*?)```', part)
                if m:
                    lang = m.group(1) or None
                    code_body = m.group(2)
                else:
                    # Fallback: strip backticks
                    code_body = part.strip('`')
                    lang = None
                # Render code block using Streamlit's code renderer (preserves raw content)
                try:
                    st.code(code_body, language=lang)
                except Exception:
                    # As a fallback, render inside a pre tag
                    safe_code = html_lib.escape(code_body)
                    st.markdown(f'<pre style="white-space:pre-wrap">{safe_code}</pre>', unsafe_allow_html=True)
            else:
                # Non-code segment: clean response (converts markdown headers into styled HTML)
                cleaned = _clean_response(part)
                if cleaned and cleaned.strip():
                    st.markdown(cleaned, unsafe_allow_html=True)

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

# Inject Phosphor Icons
st.markdown("<script src='https://unpkg.com/@phosphor-icons/web'></script>", unsafe_allow_html=True)

if not auth.require_auth():
    st.stop()

user_email = auth.get_user_email()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo block
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:24px'>"
        "<div style='width:24px;height:24px;background:#C1943C;border-radius:6px;display:flex;align-items:center;justify-content:center;flex-shrink:0'>"
        "<i class='ph ph-shield-check' style='color:#0D0B07;font-size:16px'></i>"
        "</div>"
        "<span class='sidebar-logo-text'>SecurCoach AI</span>"
        "</div>",
        unsafe_allow_html=True
    )

    # Page navigation
    active_page = st.radio(
        "Navigate",
        ["💬 Chat", "📝 Quiz", "📊 Progress"],
        index=["💬 Chat", "📝 Quiz", "📊 Progress"].index(st.session_state.active_page)
              if st.session_state.active_page in ["💬 Chat", "📝 Quiz", "📊 Progress"] else 0,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.active_page = active_page
    st.divider()

    # Domain selector
    st.session_state.selected_domain = st.selectbox(
        "Learning Domain",
        llm_engine.DOMAINS,
        index=llm_engine.DOMAINS.index(st.session_state.selected_domain)
              if st.session_state.selected_domain in llm_engine.DOMAINS else 0,
        help="Focus the AI's training on a specific security domain.",
    )
    if st.session_state.messages:
        st.warning(
            f"Switching domain will change the AI's context. "
            "Start a new conversation for the best results."
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Model selector (Advanced Settings)
    with st.expander("⚙️ Advanced Settings"):
        st.session_state.selected_model = st.selectbox(
            "AI Model",
            llm_engine.MODEL_NAMES,
            index=llm_engine.MODEL_NAMES.index(st.session_state.selected_model) 
                  if st.session_state.selected_model in llm_engine.MODEL_NAMES else 0,
            help="Switch between different models.",
            label_visibility="collapsed"
        )
    
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Lab Mode Toggle Callback
    def _on_lab_mode_change():
        if st.session_state.get("messages"):
            st.toast("Switched Lab Mode. Start a new conversation for a fresh scenario.", icon="🧪")

    # Lab Mode Toggle
    st.toggle(
        "🧪 Hands-On Lab Mode",
        key="lab_mode",
        help="Practice in a live terminal environment",
        on_change=_on_lab_mode_change
    )

    st.divider()

    # New conversation
    if st.button("＋  New conversation", use_container_width=True):
        _new_conversation()
        _refresh_conversations(force=True)
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Conversation search
    search_query = st.text_input(
        "Search conversations",
        value=st.session_state.get("search_query", ""),
        placeholder="\U0001f50d Search...",
        label_visibility="collapsed",
        key="conv_search_input",
    )
    st.session_state.search_query = search_query

    # Conversation list
    summaries = st.session_state.get("conversation_summaries", [])
    if search_query.strip():
        q = search_query.strip().lower()
        summaries = [s for s in summaries if q in s.get("title", "").lower()]
    current_cid = st.session_state.current_conversation_id

    # Initials block moved to bottom

    if summaries:
        grouped = _group_conversations(summaries)
        for group_name, items in grouped.items():
            st.markdown(f"<small style='color:var(--color-text-muted)'>{group_name}</small>", unsafe_allow_html=True)
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
        with st.container(border=True):
            st.markdown(
                "<div style='text-align: center; margin-bottom: 12px;'>"
                "<p style='color: var(--color-text-bright); font-size: 13px; font-weight: 600; margin-bottom: 4px;'>No conversations</p>"
                "<p style='color: var(--color-text-muted); font-size: 12px; line-height: 1.4;'>Start a secure session to begin.</p>"
                "</div>", unsafe_allow_html=True
            )
            if st.button("⚡ Start your first session", use_container_width=True, type="primary"):
                _new_conversation()
                st.rerun()

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

    # Sidebar Footer: Initials Avatar
    st.markdown("<div style='margin-top:auto;padding-top:20px'></div>", unsafe_allow_html=True)
    initials = "".join([n[0] for n in user_email.split("@")[0].split(".") if n])[:2].upper() or "MR"
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;padding:4px 2px'>"
        f"<div style='width:28px;height:28px;border-radius:50%;background:#1A1508;border:0.5px solid rgba(193,148,60,0.3);display:flex;align-items:center;justify-content:center;font-family:\"Space Grotesk\";font-size:10px;font-weight:500;color:#C1943C'>"
        f"{initials}</div>"
        f"<div style='font-family:\"Space Grotesk\";font-size:11px;color:var(--color-text-muted);letter-spacing:0.02em'>"
        f"{html_lib.escape(user_email)}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

# ── Page dispatch ─────────────────────────────────────────────────────────────
if st.session_state.active_page == "📝 Quiz":
    quiz.render_quiz(user_email)
    st.stop()

if st.session_state.active_page == "📊 Progress":
    progress.render_progress(user_email)
    st.stop()

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<header style='display:flex;align-items:center;justify-content:space-between;height:52px;padding:0 var(--spacing-xl);border-bottom:0.5px solid var(--color-border);background:var(--color-surface);margin:-1rem -1rem 1rem -1rem'>"
    f"<div style='display:flex;align-items:center;gap:var(--spacing-base)'>"
    f"<span style='font-family:var(--font-heading);font-weight:600;font-size:14px;color:var(--color-accent-gold);text-transform:capitalize;letter-spacing:0.04em'>{html_lib.escape(st.session_state.selected_domain)}</span>"
    f"</div>"
    f"<div style='display:flex;align-items:center;gap:var(--spacing-sm)'>"
    f"<i class='ph ph-cpu' style='font-size:13px;color:var(--color-text-muted)'></i>"
    f"<span style='font-family:var(--font-heading);font-weight:500;font-size:12px;color:var(--color-text-muted)'>Model: {html_lib.escape(st.session_state.selected_model)}</span>"
    f"</div>"
    f"</header>", 
    unsafe_allow_html=True
)

# DB error banner
db_err = db.get_error()
if db_err:
    st.markdown(f'<div class="err-banner">⚠️ Database error: {html_lib.escape(db_err)}</div>', unsafe_allow_html=True)
    db.clear_error()

st.divider()

# ── Suggested questions (when chat is empty) ──────────────────────────────────
if not st.session_state.messages and not st.session_state.get("pending_prompt"):
    suggestions = llm_engine.get_suggestions(st.session_state.selected_domain, lab_mode=st.session_state.lab_mode)
    if suggestions:
        mode_label = "Lab challenges" if st.session_state.lab_mode else "Getting started"
        st.markdown(
            f"<p style='color:var(--color-text-muted);margin-bottom:12px'>"
                f"{mode_label} with <strong style='color:var(--color-accent-gold)'>"
                f"{st.session_state.selected_domain}</strong>:</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(suggestions))
        for col, q in zip(cols, suggestions):
            with col:
                if st.button(q, use_container_width=True, key=f"sug_{q[:20]}"):
                    st.session_state.pending_prompt = q
                    st.rerun()

    if st.session_state.lab_mode:
        empty_hint = "Pick a challenge above — or describe what you want to practice."
    else:
        empty_hint = "Ask anything about cybersecurity — or pick a suggestion above."
    st.markdown(
        f"<div style='text-align:center;padding:3rem 0 1rem;"
        f"color:var(--color-text-muted);font-size:.9rem'>"
        f"{empty_hint}</div>",
        unsafe_allow_html=True,
    )

# ── Message history ───────────────────────────────────────────────────────────
chat_container = st.container()

# Context truncation warning
if len(st.session_state.messages) > 20:
    st.markdown(
        '<div class="ctx-warning">' 
        '⚠️ The AI is referencing your last 20 messages. '
        'Earlier context in this conversation may not be available.'
        '</div>',
        unsafe_allow_html=True,
    )

with chat_container:
    for msg in st.session_state.messages:
        _render_message(msg)

# ── Chat input ────────────────────────────────────────────────────────────────
if st.session_state.lab_mode:
    _placeholder = f"Describe a {st.session_state.selected_domain.lower()} scenario to practice..."
else:
    _placeholder = f"Ask about {st.session_state.selected_domain.lower()}..."
user_input = st.chat_input(
    placeholder=_placeholder,
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
    st.session_state.stop_generation = False
    is_first_exchange = not st.session_state.conv_title_set and len(st.session_state.messages) <= 2
    
    with chat_container:
        ai_placeholder = st.empty()
        stop_col, _ = st.columns([1, 5])
        stop_btn_holder = stop_col.empty()
    full_response   = ""

    try:
        # Show stop button once before starting the stream
        with stop_btn_holder:
            if st.button("⏹ Stop", key="stop_gen"):
                st.session_state.stop_generation = True

        buffer = ""
        
        # Initial loading state before first chunk
        header_html = (
            f'<div class="msg-meta">'
            f'<div class="avatar" style="width:20px;height:20px;border-radius:5px;background:#1A1508;border:0.5px solid rgba(193,148,60,0.4);display:flex;align-items:center;justify-content:center">'
            f'<i class="ph ph-shield" style="font-size:11px;color:#C1943C"></i></div>'
            f'<span class="name" style="color:var(--color-accent-gold);font-family:\'Space Grotesk\'">SecurCoach AI</span>'
            f'<span class="sep">·</span>'
            f'<span class="time">{html_lib.escape(now_ts)}</span>'
            f'</div>'
        )
        ai_placeholder.markdown(
            f'<div class="msg-ai">{header_html}\n\n<div style="display:flex;align-items:center;gap:8px;color:var(--color-accent-gold);padding:8px 0"><i class="ph ph-circle-notch ph-spin"></i><span style="font-size:13px">Thinking...</span></div></div>',
            unsafe_allow_html=True,
        )

        for chunk in llm_engine.stream_response(st.session_state.messages, request_title=is_first_exchange):
            # Check for stop
            if st.session_state.get("stop_generation"):
                break
            
            buffer += chunk
            # Clean on every chunk might be overkill, but ensures metadata is hidden immediately
            clean_buffer = _clean_response(buffer)
            full_response = clean_buffer
            
            with ai_placeholder.container():
                st.markdown(
                    f'<div class="msg-ai">{header_html}\n\n{clean_buffer}▌\n\n</div>',
                    unsafe_allow_html=True,
                )

        # Clear stop button
        stop_btn_holder.empty()

        # Final render without cursor
        if not full_response.strip():
            full_response = "⚠️ No response received. The AI may be rate-limited — please try again."
            ai_placeholder.markdown(
                f'<div class="err-banner">{full_response}</div>',
                unsafe_allow_html=True,
            )
        else:
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
        # Extract inline title if this was the first exchange
        extracted_title = None
        if is_first_exchange:
            full_response, extracted_title = llm_engine.extract_title_from_response(full_response)

        # Save AI response
        ai_msg = {"role": "assistant", "content": full_response, "timestamp": now_ts}
        st.session_state.messages.append(ai_msg)
        db.save_message(
            user_email,
            st.session_state.current_conversation_id,
            "assistant",
            full_response,
        )

        # Set conversation title on first exchange
        if is_first_exchange:
            if extracted_title:
                title = extracted_title
            else:
                words = prompt.split()
                title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            
            db.update_conversation_title(
                user_email, st.session_state.current_conversation_id, title
            )
            st.session_state.conv_title_set = True
            st.session_state.current_conv_title = title
            _refresh_conversations(force=True)


