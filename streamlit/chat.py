"""
chat.py — Google Gemini 2.0 Flash integration with streaming support.
"""
from __future__ import annotations
from typing import Generator

import google.generativeai as genai
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


def get_suggestions(domain: str) -> list[str]:
    return _SUGGESTED_QUESTIONS.get(domain, [])


def _get_client() -> genai.GenerativeModel:
    domain = st.session_state.get("selected_domain", "General Security")
    cache_key = f"gemini_client_{domain}"
    if cache_key not in st.session_state:
        genai.configure(api_key=config.gemini_api_key())
        st.session_state[cache_key] = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPTS.get(domain, _SYSTEM_PROMPTS["General Security"]),
        )
    return st.session_state[cache_key]


def _build_history(messages: list[dict]) -> list[dict]:
    """Convert our internal message format to Gemini history format (last 20 msgs)."""
    history: list[dict] = []
    # Only send last 20 messages as context — enough for coherence, avoids token bloat
    for msg in messages[-21:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


def stream_response(messages: list[dict]) -> Generator[str, None, None]:
    """
    Yields text chunks from Gemini for the last message in `messages`.
    Raises on API errors so the caller can display them.
    """
    if not messages:
        return

    client = _get_client()
    history = _build_history(messages)
    prompt  = messages[-1]["content"]

    chat = client.start_chat(history=history)
    response = chat.send_message(prompt, stream=True)

    for chunk in response:
        text = chunk.text
        if text:
            yield text


def generate_title(first_message: str) -> str:
    """Generate a short 4-6 word title for a cybersecurity chat."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content(
            f"Create a short 4-6 word title for a cybersecurity chat starting with: "
            f'"{first_message[:200]}". Reply with only the title.',
            request_options={"timeout": 5},  # don't wait more than 5s
        )
        title = result.text.strip().strip('"').strip("'")
        return title[:60] if title else first_message[:40]
    except Exception:
        return first_message[:40]  # silent fallback, never blocks
