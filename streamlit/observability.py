"""Optional observability helpers backed by Langfuse.

This module is intentionally defensive: if Langfuse is not installed,
or env/secrets are missing, all functions safely no-op.
"""
from __future__ import annotations

from typing import Any
import streamlit as st

import config

try:
    from langfuse import Langfuse
except Exception:  # pragma: no cover - optional dependency/runtime
    Langfuse = None  # type: ignore[assignment]


def _enabled() -> bool:
    return bool(config.langfuse_public_key() and config.langfuse_secret_key())


def get_client() -> Any | None:
    if not _enabled() or Langfuse is None:
        return None

    if "langfuse_client" in st.session_state:
        return st.session_state["langfuse_client"]

    try:
        client = Langfuse(
            public_key=config.langfuse_public_key(),
            secret_key=config.langfuse_secret_key(),
            host=config.langfuse_host(),
        )
        st.session_state["langfuse_client"] = client
        return client
    except Exception:
        return None


def start_trace(name: str, user_id: str | None = None, metadata: dict[str, Any] | None = None) -> Any | None:
    client = get_client()
    if client is None:
        return None
    try:
        return client.trace(name=name, user_id=user_id, metadata=metadata or {})
    except Exception:
        return None


def log_generation(
    trace: Any | None,
    name: str,
    model: str,
    input_payload: Any,
    output_payload: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if trace is None:
        return
    try:
        trace.generation(
            name=name,
            model=model,
            input=input_payload,
            output=output_payload,
            metadata=metadata or {},
        )
    except Exception:
        pass


def log_tool_call(
    trace: Any | None,
    tool_name: str,
    tool_input: str,
    tool_output: str,
) -> None:
    if trace is None:
        return
    try:
        trace.span(
            name=f"tool:{tool_name}",
            input={"input": tool_input},
            output={"output": tool_output},
        )
    except Exception:
        pass


def flush() -> None:
    client = get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception:
        pass
