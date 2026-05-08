"""
quiz.py — Skill assessment quiz with 5 questions per security domain.
All answers have been verified for accuracy.
"""
from __future__ import annotations

import streamlit as st
import html as html_lib

import db
import chat

# ── Quiz questions ────────────────────────────────────────────────────────────
# Each question: q, options (list of 4), answer (0-indexed), explanation

QUIZ_QUESTIONS: dict[str, list[dict]] = {
    "General Security": [
        {
            "q": "What does the 'C' in the CIA triad stand for?",
            "options": ["Compliance", "Confidentiality", "Cybersecurity", "Continuity"],
            "answer": 1,
            "explanation": "The CIA triad consists of Confidentiality, Integrity, and Availability — the three core principles of information security.",
        },
        {
            "q": "The principle of least privilege states that users should:",
            "options": [
                "Have admin access for convenience",
                "Share credentials with their team",
                "Be given only the minimum access needed to perform their job",
                "Use the same password across all systems",
            ],
            "answer": 2,
            "explanation": "Least privilege minimizes the attack surface by ensuring each user has only the permissions they need — nothing more.",
        },
        {
            "q": "Zero Trust architecture assumes:",
            "options": [
                "Internal network traffic is always safe",
                "No user or device is trusted by default, regardless of location",
                "Only external traffic needs inspection",
                "VPN connections are inherently secure",
            ],
            "answer": 1,
            "explanation": "Zero Trust operates on 'never trust, always verify' — every request is authenticated and authorized regardless of network position.",
        },
        {
            "q": "Social engineering attacks primarily target:",
            "options": [
                "Firewall configurations",
                "Encryption algorithms",
                "Human psychology and behavior",
                "Operating system vulnerabilities",
            ],
            "answer": 2,
            "explanation": "Social engineering exploits human trust, fear, or urgency rather than technical vulnerabilities.",
        },
        {
            "q": "Defense in depth refers to:",
            "options": [
                "Using the strongest single security control available",
                "Multiple overlapping layers of security controls",
                "Deploying security only at the network perimeter",
                "Encrypting all data at rest",
            ],
            "answer": 1,
            "explanation": "Defense in depth uses multiple security layers so that if one fails, others still protect the asset.",
        },
    ],
    "Network Security": [
        {
            "q": "At which OSI layers do stateful firewalls primarily operate?",
            "options": [
                "Layer 1 (Physical) and Layer 2 (Data Link)",
                "Layer 3 (Network) and Layer 4 (Transport)",
                "Layer 5 (Session) and Layer 6 (Presentation)",
                "Layer 7 (Application) only",
            ],
            "answer": 1,
            "explanation": "Stateful firewalls inspect packets at Layers 3 and 4, tracking connection state via IP addresses and TCP/UDP ports.",
        },
        {
            "q": "What is the primary purpose of a VLAN?",
            "options": [
                "Encrypting network traffic",
                "Logically segmenting a network at Layer 2",
                "Providing wireless access points",
                "Replacing physical routers",
            ],
            "answer": 1,
            "explanation": "VLANs create isolated broadcast domains on the same physical switch, segmenting traffic without separate hardware.",
        },
        {
            "q": "TCP port 443 is the default port for:",
            "options": ["HTTP", "SSH", "HTTPS", "DNS"],
            "answer": 2,
            "explanation": "Port 443 is used for HTTPS — HTTP encrypted with TLS. Port 80 is unencrypted HTTP.",
        },
        {
            "q": "What is the key difference between an IDS and an IPS?",
            "options": [
                "IDS encrypts traffic; IPS decrypts it",
                "IDS detects and alerts; IPS can also block malicious traffic",
                "IDS is hardware-based; IPS is software-based",
                "There is no difference — the terms are interchangeable",
            ],
            "answer": 1,
            "explanation": "An IDS (Intrusion Detection System) monitors and alerts; an IPS (Intrusion Prevention System) can actively block threats inline.",
        },
        {
            "q": "ARP spoofing is an attack that targets which OSI layer?",
            "options": [
                "Layer 1 (Physical)",
                "Layer 2 (Data Link)",
                "Layer 4 (Transport)",
                "Layer 7 (Application)",
            ],
            "answer": 1,
            "explanation": "ARP operates at Layer 2. ARP spoofing sends falsified ARP messages to link the attacker's MAC with a legitimate IP address.",
        },
    ],
    "Web App Security": [
        {
            "q": "SQL injection exploits:",
            "options": [
                "Weak password policies",
                "Unsanitized user input concatenated into SQL queries",
                "Missing HTTPS certificates",
                "Outdated JavaScript libraries",
            ],
            "answer": 1,
            "explanation": "SQLi occurs when untrusted input is embedded directly into SQL queries without parameterization or escaping.",
        },
        {
            "q": "Which OWASP Top 10 (2021) category is ranked #1?",
            "options": [
                "Injection",
                "Cryptographic Failures",
                "Broken Access Control",
                "Security Misconfiguration",
            ],
            "answer": 2,
            "explanation": "A01:2021 is Broken Access Control. Injection dropped to A03:2021 in the latest ranking.",
        },
        {
            "q": "Cross-Site Request Forgery (CSRF) exploits:",
            "options": [
                "The browser's automatic inclusion of cookies with requests to the origin site",
                "Weak encryption algorithms",
                "Open redirect vulnerabilities",
                "DNS poisoning",
            ],
            "answer": 0,
            "explanation": "CSRF tricks a user's browser into sending an authenticated request to a site where they're logged in, using the browser's automatic cookie handling.",
        },
        {
            "q": "A Content Security Policy (CSP) header primarily defends against:",
            "options": [
                "SQL Injection",
                "Brute-force attacks",
                "Cross-Site Scripting (XSS) and data injection",
                "Denial of Service",
            ],
            "answer": 2,
            "explanation": "CSP restricts which sources can serve content (scripts, styles, images), mitigating XSS by blocking inline scripts and unauthorized origins.",
        },
        {
            "q": "Stored XSS differs from reflected XSS in that:",
            "options": [
                "Stored XSS is less dangerous",
                "The malicious script is persisted on the server (e.g., in a database)",
                "Stored XSS only affects the attacker",
                "Reflected XSS requires physical access",
            ],
            "answer": 1,
            "explanation": "Stored (persistent) XSS saves the payload server-side. Every user who views the affected page is attacked, unlike reflected XSS which requires a crafted URL.",
        },
    ],
    "Cloud Security": [
        {
            "q": "In the Shared Responsibility Model, who is responsible for configuring IAM policies?",
            "options": [
                "The cloud provider (e.g., AWS)",
                "The customer",
                "Both equally",
                "Neither — IAM is automatic",
            ],
            "answer": 1,
            "explanation": "The cloud provider secures the infrastructure 'of' the cloud; the customer is responsible for security 'in' the cloud, including IAM configuration.",
        },
        {
            "q": "By default, AWS S3 buckets are:",
            "options": [
                "Publicly readable",
                "Publicly writable",
                "Private (no public access)",
                "Read-only for authenticated AWS users",
            ],
            "answer": 2,
            "explanation": "Since 2023, S3 buckets block all public access by default. Public access must be explicitly enabled.",
        },
        {
            "q": "Infrastructure as Code (IaC) security scanning catches issues:",
            "options": [
                "Only after deployment to production",
                "Before deployment, by analyzing configuration templates",
                "Only in the application code layer",
                "Only during penetration testing",
            ],
            "answer": 1,
            "explanation": "IaC scanning (e.g., Checkov, tfsec) analyzes Terraform/CloudFormation templates pre-deployment to catch misconfigurations early.",
        },
        {
            "q": "What is the primary risk of an overly permissive IAM policy using '*' for actions and resources?",
            "options": [
                "It improves performance",
                "It violates least privilege, granting unrestricted access to all services",
                "It only affects billing",
                "It has no security impact",
            ],
            "answer": 1,
            "explanation": "A policy with Action: '*' and Resource: '*' grants god-mode access. If compromised, the attacker can do anything in the account.",
        },
        {
            "q": "AWS GuardDuty is a service that provides:",
            "options": [
                "Web application firewall capabilities",
                "Intelligent threat detection using ML and anomaly detection",
                "Data encryption at rest",
                "Container orchestration",
            ],
            "answer": 1,
            "explanation": "GuardDuty continuously monitors AWS accounts for malicious activity using threat intelligence, ML, and anomaly detection.",
        },
    ],
    "Cryptography": [
        {
            "q": "Symmetric encryption uses:",
            "options": [
                "Two different keys (public and private)",
                "The same key for both encryption and decryption",
                "No keys — just a password",
                "A hash function instead of a cipher",
            ],
            "answer": 1,
            "explanation": "Symmetric ciphers (AES, ChaCha20) use a single shared key. Asymmetric ciphers (RSA, ECC) use a key pair.",
        },
        {
            "q": "Why should password hashes be salted?",
            "options": [
                "To make passwords longer",
                "To prevent rainbow table and precomputed hash attacks",
                "To encrypt the hash",
                "Salt has no security benefit",
            ],
            "answer": 1,
            "explanation": "A unique random salt per password ensures identical passwords produce different hashes, defeating rainbow tables.",
        },
        {
            "q": "ECB (Electronic Codebook) mode is considered insecure because:",
            "options": [
                "It uses too many rounds of encryption",
                "Identical plaintext blocks always produce identical ciphertext blocks",
                "It requires too much computational power",
                "It only works with RSA",
            ],
            "answer": 1,
            "explanation": "ECB encrypts each block independently, so patterns in plaintext are visible in ciphertext (the 'ECB penguin' problem).",
        },
        {
            "q": "TLS 1.3 improved upon TLS 1.2 by:",
            "options": [
                "Removing the handshake entirely",
                "Reducing the handshake to 1 round trip (1-RTT) and removing weak cipher suites",
                "Using only symmetric encryption",
                "Eliminating certificate requirements",
            ],
            "answer": 1,
            "explanation": "TLS 1.3 achieves a 1-RTT handshake (vs 2-RTT), removed RC4, 3DES, and SHA-1, and supports only AEAD ciphers.",
        },
        {
            "q": "Which algorithm is recommended for password hashing in 2024?",
            "options": [
                "MD5",
                "SHA-256",
                "bcrypt, scrypt, or Argon2",
                "AES-256",
            ],
            "answer": 2,
            "explanation": "bcrypt, scrypt, and Argon2 are designed for password hashing — they're intentionally slow and memory-hard. SHA-256/MD5 are too fast.",
        },
    ],
    "Incident Response": [
        {
            "q": "According to NIST SP 800-61, what is the FIRST phase of incident response?",
            "options": [
                "Detection and Analysis",
                "Containment",
                "Preparation",
                "Recovery",
            ],
            "answer": 2,
            "explanation": "NIST defines four phases: (1) Preparation, (2) Detection & Analysis, (3) Containment, Eradication & Recovery, (4) Post-Incident Activity.",
        },
        {
            "q": "Chain of custody documentation is important because it ensures:",
            "options": [
                "Faster incident resolution",
                "Legal admissibility of digital evidence in court",
                "Automatic backup of evidence",
                "That evidence is encrypted",
            ],
            "answer": 1,
            "explanation": "Chain of custody tracks who handled evidence, when, and how — ensuring it's admissible in legal proceedings.",
        },
        {
            "q": "When collecting forensic evidence, volatile data should be collected:",
            "options": [
                "Last, after disk images",
                "Only if a warrant is available",
                "First, because it is lost when the system is powered off",
                "Never — only non-volatile data matters",
            ],
            "answer": 2,
            "explanation": "The order of volatility (RFC 3227): registers → cache → RAM → disk. Volatile data like running processes and network connections are lost on shutdown.",
        },
        {
            "q": "An IOC (Indicator of Compromise) is:",
            "options": [
                "A type of firewall rule",
                "An artifact that indicates a system may have been breached (e.g., suspicious IPs, file hashes)",
                "A software update patch",
                "A user authentication method",
            ],
            "answer": 1,
            "explanation": "IOCs are forensic artifacts — malicious IPs, domain names, file hashes, registry changes — that indicate a compromise has occurred.",
        },
        {
            "q": "The primary purpose of a post-incident review (lessons learned) is to:",
            "options": [
                "Assign blame to the responsible team",
                "Identify what worked, what didn't, and improve future response",
                "Delete all evidence of the incident",
                "Notify the media",
            ],
            "answer": 1,
            "explanation": "Blameless post-mortems focus on improving detection, response, and prevention — not punishing individuals.",
        },
    ],
}


def render_quiz(user_email: str) -> None:
    """Render the skill assessment quiz UI."""
    st.markdown("# 📝 Skill Assessment")
    st.markdown(
        "<p style='color:var(--text2)'>Test your knowledge across security domains. "
        "5 questions per domain, results tracked over time.</p>",
        unsafe_allow_html=True,
    )

    # Domain selector for quiz
    quiz_domain = st.selectbox(
        "Select a domain to test",
        chat.DOMAINS,
        key="quiz_domain_select",
    )

    questions = QUIZ_QUESTIONS.get(quiz_domain, [])
    if not questions:
        st.warning("No questions available for this domain.")
        return

    # Check for existing results
    existing = db.get_quiz_results(user_email)
    domain_scores = {r["domain"]: r for r in existing} if existing else {}

    if quiz_domain in domain_scores:
        prev = domain_scores[quiz_domain]
        st.markdown(
            f"<div class='quiz-prev-score'>"
            f"Previous best: <strong>{prev['score']}/{prev['total']}</strong> "
            f"({prev['score'] * 100 // prev['total']}%)"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Quiz form
    with st.form(key=f"quiz_form_{quiz_domain}"):
        answers: list[int] = []
        for i, q in enumerate(questions):
            st.markdown(
                f"<div class='quiz-question'>"
                f"<strong>Q{i+1}.</strong> {html_lib.escape(q['q'])}"
                f"</div>",
                unsafe_allow_html=True,
            )
            choice = st.radio(
                f"Question {i+1}",
                q["options"],
                key=f"quiz_{quiz_domain}_{i}",
                label_visibility="collapsed",
            )
            answers.append(q["options"].index(choice) if choice else -1)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Submit Quiz", use_container_width=True)

    if submitted:
        score = 0
        st.divider()
        st.markdown("## Results")

        for i, q in enumerate(questions):
            correct = answers[i] == q["answer"]
            if correct:
                score += 1
            icon = "✅" if correct else "❌"
            st.markdown(
                f"**Q{i+1}.** {icon} {html_lib.escape(q['q'])}",
            )
            if not correct:
                st.markdown(
                    f"<div class='quiz-explanation'>"
                    f"Your answer: {html_lib.escape(q['options'][answers[i]])}  \n"
                    f"Correct: **{html_lib.escape(q['options'][q['answer']])}**  \n"
                    f"_{html_lib.escape(q['explanation'])}_"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='quiz-explanation correct'>"
                    f"_{html_lib.escape(q['explanation'])}_"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        pct = score * 100 // len(questions)
        if pct >= 80:
            grade_color = "var(--accent2)"
            grade_label = "Excellent"
        elif pct >= 60:
            grade_color = "var(--accent)"
            grade_label = "Good"
        else:
            grade_color = "var(--danger)"
            grade_label = "Needs Practice"

        st.markdown(
            f"<div class='quiz-score-card'>"
            f"<div class='quiz-score-num' style='color:{grade_color}'>{score}/{len(questions)}</div>"
            f"<div class='quiz-score-label' style='color:{grade_color}'>{grade_label} — {pct}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Save to DB
        db.save_quiz_result(user_email, quiz_domain, score, len(questions))
