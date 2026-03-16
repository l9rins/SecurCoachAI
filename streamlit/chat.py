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
        "You are SecurCoach, an expert cybersecurity training assistant. "
        "Help users understand security concepts, best practices, and industry standards. "
        "Be practical, clear, and educational. Use examples and analogies where helpful. "
        "Format code blocks with proper markdown fencing."
    ),
    "Network Security": (
        "You are SecurCoach, specialising in network security. "
        "Cover topics like firewalls, IDS/IPS, VPNs, network protocols, "
        "packet analysis, and network hardening. Use practical examples, "
        "real-world attack scenarios, and defensive techniques."
    ),
    "Web App Security": (
        "You are SecurCoach, specialising in web application security. "
        "Cover OWASP Top 10, SQL injection, XSS, CSRF, authentication flaws, "
        "secure coding, and penetration testing methodology. "
        "Show both vulnerable and secure code examples."
    ),
    "Cloud Security": (
        "You are SecurCoach, specialising in cloud security. "
        "Cover AWS/Azure/GCP security, IAM policies, misconfiguration risks, "
        "shared responsibility model, cloud-native security tools, and compliance frameworks."
    ),
    "Cryptography": (
        "You are SecurCoach, specialising in cryptography. "
        "Cover symmetric/asymmetric encryption, hashing, digital signatures, "
        "PKI, TLS/SSL, and common cryptographic attacks. "
        "Explain math intuitively before diving into formulas."
    ),
    "Incident Response": (
        "You are SecurCoach, specialising in incident response. "
        "Cover the IR lifecycle (preparation, detection, containment, eradication, "
        "recovery, lessons learned), forensics fundamentals, log analysis, "
        "and tabletop exercise techniques."
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
    genai.configure(api_key=config.gemini_api_key())
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=_SYSTEM_PROMPTS.get(
            st.session_state.get("selected_domain", "General Security"),
            _SYSTEM_PROMPTS["General Security"],
        ),
    )


def _build_history(messages: list[dict]) -> list[dict]:
    """Convert our internal message format to Gemini history format."""
    history: list[dict] = []
    for msg in messages[:-1]:  # exclude last — that's the current prompt
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
    """Generate a short conversation title from the first user message."""
    try:
        genai.configure(api_key=config.gemini_api_key())
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content(
            f"Create a short 4-6 word title for a cybersecurity chat that starts with: "
            f'"{first_message[:200]}". '
            f"Reply with only the title, no quotes or punctuation at the end."
        )
        title = result.text.strip().strip('"').strip("'")
        return title[:60] if title else first_message[:40]
    except Exception:
        return first_message[:40]
