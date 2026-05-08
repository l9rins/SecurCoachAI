"""
db.py — Supabase REST helpers for chat history.
All errors are surfaced via st.session_state["db_error"] and logged.
"""
from __future__ import annotations
from datetime import datetime
from urllib.parse import quote
from uuid import uuid4

import streamlit as st
import requests

import config


# ── Low-level request ─────────────────────────────────────────────────────────

def _req(
    method: str,
    path: str,
    payload: dict | None = None,
    query: str = "",
    extra_headers: dict | None = None,
) -> list | dict | None:
    base = config.supabase_url()
    key  = config.supabase_key()
    if not base or not key:
        _set_error("Supabase URL or key not configured.")
        return None

    url = f"{base}/rest/v1/{path}"
    if query:
        url = f"{url}?{query}"

    headers: dict = {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    for attempt in range(2):
        try:
            resp = requests.request(
                method, url, headers=headers, json=payload, timeout=20
            )
            resp.raise_for_status()
            return resp.json() if resp.text.strip() else None
        except requests.HTTPError as exc:
            if attempt == 1:
                _set_error(f"Supabase HTTP {exc.response.status_code}: {exc.response.text[:200]}")
            if exc.response.status_code >= 500:
                continue  # Retry on server errors
            return None
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == 1:
                _set_error(f"Supabase connection error: {str(exc)}")
            continue  # Retry on connection issues
        except Exception as exc:
            if attempt == 1:
                _set_error(str(exc))
            return None
    return None


def _set_error(msg: str) -> None:
    st.session_state["db_error"] = msg


def clear_error() -> None:
    st.session_state.pop("db_error", None)


def get_error() -> str | None:
    return st.session_state.get("db_error")


# ── Conversation summaries ────────────────────────────────────────────────────

def load_conversation_summaries(user_id: str) -> list[dict]:
    query = (
        f"select=conversation_id,title,created_at"
        f"&user_id=eq.{quote(user_id, safe='')}"
        f"&order=created_at.desc"
        f"&limit=2000"
    )
    rows = _req("GET", config.chat_history_table(), query=query)
    if not isinstance(rows, list):
        return []

    seen: set[str] = set()
    titles: dict[str, str] = {}

    for row in rows:
        cid = str(row.get("conversation_id", "")).strip()
        if cid and cid not in titles and row.get("title"):
            titles[cid] = str(row["title"])

    summaries: list[dict] = []
    for row in rows:
        cid = str(row.get("conversation_id", "")).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        title = titles.get(cid, "New conversation")
        summaries.append(
            {
                "conversation_id": cid,
                "title": title,
                "created_at": str(row.get("created_at", "")).strip(),
            }
        )
    return summaries


def load_messages_for_conversation(user_id: str, conversation_id: str) -> list[dict]:
    query = (
        f"select=sender,message,created_at"
        f"&user_id=eq.{quote(user_id, safe='')}"
        f"&conversation_id=eq.{quote(conversation_id, safe='')}"
        f"&order=created_at.desc"   # newest first
        f"&limit=100"               # last 100 messages
    )
    rows = _req("GET", config.chat_history_table(), query=query)
    if not isinstance(rows, list):
        return []

    # Then reverse in Python so they display oldest→newest
    rows = list(reversed(rows))

    messages: list[dict] = []
    for row in rows:
        created_at = str(row.get("created_at", ""))
        messages.append(
            {
                "role": "user" if str(row.get("sender", "")).lower() == "user" else "assistant",
                "content": str(row.get("message", "")),
                "timestamp": created_at[11:16] if "T" in created_at else "",
            }
        )
    return messages


def save_message(
    user_id: str,
    conversation_id: str,
    role: str,
    content: str,
) -> None:
    payload: dict = {
        "user_id":         user_id,
        "conversation_id": conversation_id,
        "sender":          "user" if role == "user" else "ai",
        "message":         content,
    }
    _req(
        "POST",
        config.chat_history_table(),
        payload=payload,
        extra_headers={"Prefer": "return=minimal"},
    )


def update_conversation_title(
    user_id: str, conversation_id: str, title: str
) -> None:
    query = (
        f"user_id=eq.{quote(user_id, safe='')}"
        f"&conversation_id=eq.{quote(conversation_id, safe='')}"
    )
    _req(
        "PATCH",
        config.chat_history_table(),
        payload={"title": title},
        query=query,
        extra_headers={"Prefer": "return=minimal"},
    )


def delete_conversation(user_id: str, conversation_id: str) -> None:
    query = (
        f"user_id=eq.{quote(user_id, safe='')}"
        f"&conversation_id=eq.{quote(conversation_id, safe='')}"
    )
    _req(
        "DELETE",
        config.chat_history_table(),
        query=query,
        extra_headers={"Prefer": "return=minimal"},
    )


def new_conversation_id() -> str:
    return str(uuid4())


# ── Quiz results ──────────────────────────────────────────────────────────────
# Table: quiz_results (user_id text, domain text, score int, total int, created_at)

def save_quiz_result(user_id: str, domain: str, score: int, total: int) -> None:
    """Save or update a quiz result (keeps best score per domain)."""
    existing = get_quiz_results(user_id)
    if existing:
        for r in existing:
            if r["domain"] == domain and r["score"] >= score:
                return  # Don't overwrite a better score

    # Upsert: delete old + insert new (Supabase REST doesn't support upsert on non-PK)
    query = (
        f"user_id=eq.{quote(user_id, safe='')}"
        f"&domain=eq.{quote(domain, safe='')}"
    )
    _req("DELETE", config.quiz_results_table(), query=query, extra_headers={"Prefer": "return=minimal"})
    _req(
        "POST",
        config.quiz_results_table(),
        payload={"user_id": user_id, "domain": domain, "score": score, "total": total},
        extra_headers={"Prefer": "return=minimal"},
    )


def get_quiz_results(user_id: str) -> list[dict]:
    """Get all quiz results for a user (one per domain, best score)."""
    query = (
        f"select=domain,score,total,created_at"
        f"&user_id=eq.{quote(user_id, safe='')}"
        f"&order=created_at.desc"
    )
    rows = _req("GET", config.quiz_results_table(), query=query)
    if not isinstance(rows, list):
        return []
    # Deduplicate: keep best per domain
    seen: dict[str, dict] = {}
    for row in rows:
        d = str(row.get("domain", ""))
        if d not in seen or row.get("score", 0) > seen[d].get("score", 0):
            seen[d] = row
    return list(seen.values())


# ── Topic completion ──────────────────────────────────────────────────────────
# Table: completed_topics (user_id text, domain text, topic_id text, completed_at)

def save_topic_completion(user_id: str, domain: str, topic_id: str) -> None:
    """Mark a topic as completed."""
    _req(
        "POST",
        config.completed_topics_table(),
        payload={"user_id": user_id, "domain": domain, "topic_id": topic_id},
        extra_headers={"Prefer": "return=minimal"},
    )


def remove_topic_completion(user_id: str, topic_id: str) -> None:
    """Unmark a topic completion."""
    query = (
        f"user_id=eq.{quote(user_id, safe='')}"
        f"&topic_id=eq.{quote(topic_id, safe='')}"
    )
    _req("DELETE", config.completed_topics_table(), query=query, extra_headers={"Prefer": "return=minimal"})


def get_completed_topics(user_id: str) -> list[str]:
    """Get list of completed topic IDs for a user."""
    query = (
        f"select=topic_id"
        f"&user_id=eq.{quote(user_id, safe='')}"
    )
    rows = _req("GET", config.completed_topics_table(), query=query)
    if not isinstance(rows, list):
        return []
    return [str(r.get("topic_id", "")) for r in rows if r.get("topic_id")]
