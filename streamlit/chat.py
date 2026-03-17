"""
chat.py — Groq LLM integration with streaming support.
"""
from __future__ import annotations
from typing import Generator

from groq import Groq
import streamlit as st

import config

_SYSTEM_PROMPTS: dict[str, str] = {
    "General Security": (
        "You are SecurCoach, an expert cybersecurity training assistant with 15 years of industry experience. "
        "When answering:\n"
        "- Use the CIA triad (Confidentiality, Integrity, Availability) as a foundational framework when relevant.\n"
        "- Provide practical, actionable advice for both individuals and organizations.\n"
        "- Use analogies to explain complex technical concepts like zero-trust or asymmetric encryption.\n"
        "- End every answer with one follow-up question to encourage critical thinking.\n"
        "- Format code blocks with proper language-tagged fences (```python, ```bash, etc.)."
    ),
    "Network Security": (
        "You are SecurCoach, a senior Network Security Architect. When answering:\n"
        "- Reference the OSI model to explain where specific threats and defenses operate.\n"
        "- Always provide specific CLI examples (e.g., iptables, tcpdump, nmap) where applicable.\n"
        "- Discuss depth-in-defense strategies, covering firewalls, IDS/IPS, and micro-segmentation.\n"
        "- End every answer with one follow-up question about network hardening.\n"
        "- Format code and logs with proper markdown fencing."
    ),
    "Web App Security": (
        "You are SecurCoach, an expert web application security trainer with 15 years "
        "of penetration testing experience. When answering:\n"
        "- Always show both vulnerable AND secure code side by side\n"
        "- Reference the relevant OWASP Top 10 category when applicable\n"
        "- Use realistic examples, not toy code\n"
        "- End every answer with one follow-up question to deepen understanding\n"
        "- Format code with proper language-tagged fences (```python, ```javascript, etc.)\n"
        "Never give vague answers — always be specific and actionable."
    ),
    "Cloud Security": (
        "You are SecurCoach, a Cloud Security Specialist (CCSP/AWS Security). When answering:\n"
        "- Heavily emphasize the Shared Responsibility Model.\n"
        "- Provide specific IAM policy examples using JSON formatting.\n"
        "- Discuss 'Cloud Native' security tools and automation (IaC scanning, GuardDuty, etc.).\n"
        "- End every answer with one follow-up question about cloud misconfiguration.\n"
        "Focus on identity as the new perimeter."
    ),
    "Cryptography": (
        "You are SecurCoach, a cryptographer. When answering:\n"
        "- Explain the 'Why' before the 'How' (e.g., why salt a password hash?).\n"
        "- Use intuitive analogies for public/private key pairs and digital signatures.\n"
        "- Warn against 'rolling your own crypto' and recommend standard libraries (e.g., PyNaCl, Cryptography.io).\n"
        "- End every answer with one follow-up question about cryptographic implementation."
    ),
    "Incident Response": (
        "You are SecurCoach, a Lead Incident Responder. When answering:\n"
        "- Follow the SANS/NIST incident response life cycle explicitly.\n"
        "- Focus on preservation of evidence and the chain of custody.\n"
        "- Provide 'Live Response' command examples for Windows (PowerShell) and Linux.\n"
        "- End every answer with one follow-up question about disaster recovery or lessons learned."
    ),
}

DOMAINS: list[str] = list(_SYSTEM_PROMPTS.keys())

_SUGGESTED_QUESTIONS: dict[str, list[str]] = {
    "General Security": [
        "What is the CIA triad and why does it matter?",
        "How do I start a career in cybersecurity?",
        "What's the difference between a vulnerability and an exploit?",
    ],
    "Network Security": [
        "How does a stateful firewall work?",
        "What is a man-in-the-middle attack?",
        "Explain the OSI model from a security perspective.",
    ],
    "Web App Security": [
        "Walk me through a SQL injection attack step by step.",
        "How does XSS work and how do I prevent it?",
        "What is CSRF and how do tokens stop it?",
    ],
    "Cloud Security": [
        "What is the shared responsibility model in AWS?",
        "How do I audit IAM permissions for least privilege?",
        "What are the most common S3 bucket misconfigurations?",
    ],
    "Cryptography": [
        "How does RSA encryption work?",
        "What's the difference between hashing and encryption?",
        "Explain TLS handshake step by step.",
    ],
    "Incident Response": [
        "Walk me through the six phases of incident response.",
        "What logs should I collect first after a breach?",
        "How do I write a good incident post-mortem?",
    ],
}

# ── Model to use ──────────────────────────────────────────────────────────────
_MODEL = "llama-3.3-70b-versatile"  # or "mixtral-8x7b-32768", "llama3-70b-8192"


def get_suggestions(domain: str) -> list[str]:
    return _SUGGESTED_QUESTIONS.get(domain, [])


def _get_client() -> Groq:
    """Return a cached Groq client (one per session)."""
    if "groq_client" not in st.session_state:
        st.session_state["groq_client"] = Groq(api_key=config.groq_api_key())
    return st.session_state["groq_client"]


def _build_messages(messages: list[dict], domain: str) -> list[dict]:
    """Build the full message list: system prompt + last 20 turns."""
    system_prompt = _SYSTEM_PROMPTS.get(domain, _SYSTEM_PROMPTS["General Security"])
    history = []
    for msg in messages[-20:]:
        role = "user" if msg["role"] == "user" else "assistant"
        history.append({"role": role, "content": msg["content"]})
    return [{"role": "system", "content": system_prompt}] + history


def stream_response(messages: list[dict]) -> Generator[str, None, None]:
    """
    Yields text chunks from Groq for the last message in `messages`.
    Raises on API errors so the caller can display them.
    """
    if not messages:
        return

    domain = st.session_state.get("selected_domain", "General Security")
    client = _get_client()
    built  = _build_messages(messages, domain)

    stream = client.chat.completions.create(
        model=_MODEL,
        messages=built,
        stream=True,
        max_tokens=2048,
        temperature=0.7,
    )

    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text


def generate_title(first_message: str) -> str:
    """Generate a short 4-6 word title for a cybersecurity chat."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Create a short 4-6 word title for a cybersecurity chat "
                        f'starting with: "{first_message[:200]}". Reply with only the title.'
                    ),
                }
            ],
            max_tokens=20,
            temperature=0.5,
        )
        title = response.choices[0].message.content.strip().strip('"').strip("'")
        return title[:60] if title else first_message[:40]
    except Exception:
        return first_message[:40]  # silent fallback, never blocks
