"""
chat.py — Groq LLM integration with streaming support.
"""
from __future__ import annotations
import re
from typing import Generator

from groq import Groq
import streamlit as st

import config

# ── Models & Domains (Top-level for immediate init) ───────────────────────────

MODELS: dict[str, dict] = {
    "Llama 3.3 70B": {
        "id": "llama-3.3-70b-versatile",
        "desc": "",
    },
    "Llama 3.1 8B": {
        "id": "llama-3.1-8b-instant",
        "desc": "",
    },
    "Mixtral 8x7B": {
        "id": "mixtral-8x7b-32768",
        "desc": "",
    },
}

MODEL_NAMES: list[str] = list(MODELS.keys())
DEFAULT_MODEL: str = MODEL_NAMES[0]
DOMAINS: list[str] = [
    "General Security",
    "Network Security",
    "Web App Security",
    "Cloud Security",
    "Cryptography",
    "Incident Response"
]

_OUTPUT_FORMAT = (
    "\n\nAlways structure your response using these sections:\n"
    "## Answer\n[Your main explanation]\n\n"
    "## Example\n[A practical code snippet, command, or scenario — never skip this]\n\n"
    "## Think About This\n[One follow-up question to deepen understanding]\n\n"
    "Format all code blocks with proper language-tagged fences (```python, ```bash, etc.).\n"
    "Keep responses thorough but focused. Never give vague answers — always be specific and actionable.\n"
    "CRITICAL: Break your main explanation into short, readable paragraphs (maximum 2-3 sentences each) or use bullet points. NEVER output a single unbroken wall of text."
)

_SYSTEM_PROMPTS: dict[str, str] = {
    "General Security": (
        "You are SecurCoach, an expert cybersecurity training assistant with 15 years of industry experience. "
        "When answering:\n"
        "- Use the CIA triad (Confidentiality, Integrity, Availability) as a foundational framework when relevant.\n"
        "- Provide practical, actionable advice for both individuals and organizations.\n"
        "- Use analogies to explain complex technical concepts like zero-trust or asymmetric encryption."
        + _OUTPUT_FORMAT
    ),
    "Network Security": (
        "You are SecurCoach, a senior Network Security Architect. When answering:\n"
        "- Reference the OSI model to explain where specific threats and defenses operate.\n"
        "- Always provide specific CLI examples (e.g., iptables, tcpdump, nmap) where applicable.\n"
        "- Discuss depth-in-defense strategies, covering firewalls, IDS/IPS, and micro-segmentation."
        + _OUTPUT_FORMAT
    ),
    "Web App Security": (
        "You are SecurCoach, an expert web application security trainer with 15 years "
        "of penetration testing experience. When answering:\n"
        "- Always show both vulnerable AND secure code side by side\n"
        "- Reference the relevant OWASP Top 10 category when applicable\n"
        "- Use realistic examples, not toy code"
        + _OUTPUT_FORMAT
    ),
    "Cloud Security": (
        "You are SecurCoach, a Cloud Security Specialist (CCSP/AWS Security). When answering:\n"
        "- Heavily emphasize the Shared Responsibility Model.\n"
        "- Provide specific IAM policy examples using JSON formatting.\n"
        "- Discuss 'Cloud Native' security tools and automation (IaC scanning, GuardDuty, etc.).\n"
        "Focus on identity as the new perimeter."
        + _OUTPUT_FORMAT
    ),
    "Cryptography": (
        "You are SecurCoach, a cryptographer. When answering:\n"
        "- Explain the 'Why' before the 'How' (e.g., why salt a password hash?).\n"
        "- Use intuitive analogies for public/private key pairs and digital signatures.\n"
        "- Warn against 'rolling your own crypto' and recommend standard libraries (e.g., PyNaCl, Cryptography.io)."
        + _OUTPUT_FORMAT
    ),
    "Incident Response": (
        "You are SecurCoach, a Lead Incident Responder. When answering:\n"
        "- Follow the SANS/NIST incident response life cycle explicitly.\n"
        "- Focus on preservation of evidence and the chain of custody.\n"
        "- Provide 'Live Response' command examples for Windows (PowerShell) and Linux."
        + _OUTPUT_FORMAT
    ),
}



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




def get_model() -> str:
    """Return the Groq model ID from session state selection."""
    name = st.session_state.get("selected_model", DEFAULT_MODEL)
    return MODELS.get(name, MODELS[DEFAULT_MODEL])["id"]


# ── Lab mode ──────────────────────────────────────────────────────────────────

_LAB_SYSTEM_PROMPTS: dict[str, str] = {
    "General Security": (
        "You are SecurCoach Lab Master. You are running a hands-on security lab.\n"
        "Present the user with a REALISTIC scenario involving a security misconfiguration "
        "or vulnerability. Include specific details (system configs, log excerpts, or policies).\n"
        "Do NOT reveal the vulnerability upfront. Ask the user to:\n"
        "1. Identify the security issue\n"
        "2. Explain why it is dangerous\n"
        "3. Propose a remediation\n\n"
        "After they respond, evaluate their answer thoroughly. If correct, congratulate them "
        "and explain any additional nuances. If incorrect, give hints without revealing the answer."
    ),
    "Network Security": (
        "You are SecurCoach Lab Master. Present the user with a REALISTIC network scenario.\n"
        "This could be: a firewall ruleset with a flaw, a suspicious pcap/tcpdump output, "
        "a misconfigured VLAN, or an IDS alert log.\n"
        "Include actual CLI output or config snippets (iptables, Cisco ACLs, Snort rules, etc.).\n"
        "Do NOT reveal the issue. Ask the user to analyze and remediate.\n"
        "Evaluate their response step by step."
    ),
    "Web App Security": (
        "You are SecurCoach Lab Master. Present the user with a REALISTIC code snippet "
        "(Python/Flask, Node/Express, PHP, or Java) that contains EXACTLY ONE web vulnerability.\n"
        "The code should look production-quality, not a toy example. The vulnerability should be "
        "from the OWASP Top 10 (SQLi, XSS, CSRF, IDOR, SSRF, etc.).\n"
        "Do NOT label or hint at the vulnerability. Ask the user to:\n"
        "1. Identify the vulnerability and its OWASP category\n"
        "2. Show how an attacker would exploit it\n"
        "3. Write the fixed version of the code\n\n"
        "Evaluate their response against all three criteria."
    ),
    "Cloud Security": (
        "You are SecurCoach Lab Master. Present the user with a REALISTIC cloud scenario.\n"
        "This could be: an overly permissive IAM policy (JSON), a Terraform/CloudFormation "
        "snippet with a misconfiguration, an S3 bucket policy, or a security group config.\n"
        "Include actual JSON/HCL code. Do NOT reveal what is wrong.\n"
        "Ask the user to identify the misconfiguration and write the corrected version.\n"
        "Evaluate using the Shared Responsibility Model and principle of least privilege."
    ),
    "Cryptography": (
        "You are SecurCoach Lab Master. Present the user with a REALISTIC crypto scenario.\n"
        "This could be: code that uses a weak cipher, improper IV handling, ECB mode, "
        "unsalted password hashing, hardcoded keys, or broken key exchange.\n"
        "Include actual code (Python with cryptography/PyCryptodome, or Node.js crypto).\n"
        "Do NOT reveal the flaw. Ask the user to identify it and show the secure implementation.\n"
        "Evaluate their understanding of WHY the original is insecure."
    ),
    "Incident Response": (
        "You are SecurCoach Lab Master. Present the user with a REALISTIC incident scenario.\n"
        "This could be: a set of suspicious log entries (auth logs, web server logs, syslog), "
        "a timeline of events during a breach, or artifacts from a compromised system.\n"
        "Include realistic timestamps, IPs, user agents, and file paths.\n"
        "Do NOT reveal what happened. Ask the user to:\n"
        "1. Determine what type of attack occurred\n"
        "2. Identify the indicators of compromise (IOCs)\n"
        "3. Outline their response plan following NIST/SANS phases\n\n"
        "Evaluate their incident response methodology."
    ),
}

_LAB_SUGGESTIONS: dict[str, list[str]] = {
    "General Security": [
        "Give me a security misconfiguration to analyze",
        "Test me on access control flaws",
        "Challenge me with a social engineering scenario",
    ],
    "Network Security": [
        "Show me a suspicious firewall config",
        "Give me a packet capture to analyze",
        "Test me with a network intrusion scenario",
    ],
    "Web App Security": [
        "Give me vulnerable code to find the bug",
        "Test me on SQL injection",
        "Challenge me with an XSS vulnerability",
    ],
    "Cloud Security": [
        "Show me a misconfigured IAM policy",
        "Give me a Terraform config to audit",
        "Test me on S3 bucket security",
    ],
    "Cryptography": [
        "Give me code with a crypto flaw to find",
        "Test me on password hashing mistakes",
        "Challenge me with a broken encryption implementation",
    ],
    "Incident Response": [
        "Give me suspicious logs to investigate",
        "Test me with a breach timeline",
        "Challenge me with a ransomware scenario",
    ],
}


def get_suggestions(domain: str, lab_mode: bool = False) -> list[str]:
    """Return domain-specific suggested questions for chat or lab mode."""
    if lab_mode:
        return _LAB_SUGGESTIONS.get(domain, [])
    return _SUGGESTED_QUESTIONS.get(domain, [])


def _get_client() -> Groq:
    """Return a cached Groq client (one per session)."""
    if "groq_client" not in st.session_state:
        st.session_state["groq_client"] = Groq(api_key=config.groq_api_key())
    return st.session_state["groq_client"]


def _build_messages(messages: list[dict], domain: str, lab_mode: bool = False) -> list[dict]:
    """Build the full message list: system prompt + last 20 turns."""
    if lab_mode:
        system_prompt = _LAB_SYSTEM_PROMPTS.get(domain, _LAB_SYSTEM_PROMPTS["General Security"])
    else:
        system_prompt = _SYSTEM_PROMPTS.get(domain, _SYSTEM_PROMPTS["General Security"])
    history = []
    for msg in messages[-20:]:
        role = "user" if msg["role"] == "user" else "assistant"
        history.append({"role": role, "content": msg["content"]})
    return [{"role": "system", "content": system_prompt}] + history


def stream_response(messages: list[dict], request_title: bool = False) -> Generator[str, None, None]:
    """
    Yields text chunks from Groq for the last message in `messages`.
    If request_title=True, appends a title-generation instruction so the
    AI includes a TITLE: line at the end — saving a separate API call.
    Raises on API errors so the caller can display them.
    """
    if not messages:
        return

    domain = st.session_state.get("selected_domain", "General Security")
    client = _get_client()
    lab_mode = st.session_state.get("lab_mode", False)
    built  = _build_messages(messages, domain, lab_mode=lab_mode)

    if request_title:
        built.append({
            "role": "user",
            "content": (
                "After your full response, on a NEW line at the very end, "
                "write exactly: TITLE: [a short 4-6 word title for this conversation]. "
                "Do not include any other text on that line."
            ),
        })

    stream = client.chat.completions.create(
        model=get_model(),
        messages=built,
        stream=True,
        max_tokens=4096,
        temperature=0.7,
    )

    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text




_TITLE_PATTERN = re.compile(r'\n*TITLE:\s*(.+)$', re.MULTILINE)


def extract_title_from_response(response: str) -> tuple[str, str | None]:
    """
    If the response contains a TITLE: line, strip it and return
    (clean_response, title). Otherwise return (response, None).
    """
    match = _TITLE_PATTERN.search(response)
    if match:
        title = match.group(1).strip().strip('"').strip("'")[:60]
        clean = response[:match.start()].rstrip()
        return clean, title if title else None
    return response, None


def generate_title(first_message: str) -> str:
    """Fallback: generate a title via a separate API call (used only if inline extraction fails)."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=get_model(),
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

