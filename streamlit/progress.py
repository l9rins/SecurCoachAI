"""
progress.py — Progress dashboard and learning paths.
"""
from __future__ import annotations

import streamlit as st
import html as html_lib

import db
import chat

# ── Learning paths: 5 topics per domain ───────────────────────────────────────

LEARNING_PATHS: dict[str, list[dict]] = {
    "General Security": [
        {"id": "gs_cia", "title": "CIA Triad Fundamentals", "prompt": "Explain the CIA triad in cybersecurity with real-world examples for each pillar."},
        {"id": "gs_authn", "title": "Authentication vs. Authorization", "prompt": "What is the difference between authentication and authorization? Give examples of each."},
        {"id": "gs_zt", "title": "Zero Trust Architecture", "prompt": "Explain Zero Trust architecture. How does it differ from traditional perimeter security?"},
        {"id": "gs_se", "title": "Social Engineering Defense", "prompt": "What are the main types of social engineering attacks and how do you defend against them?"},
        {"id": "gs_fw", "title": "Security Frameworks (NIST, ISO)", "prompt": "Compare NIST CSF and ISO 27001. When would you use each framework?"},
    ],
    "Network Security": [
        {"id": "ns_osi", "title": "OSI Model & TCP/IP", "prompt": "Explain the 7 layers of the OSI model and how attacks target each layer."},
        {"id": "ns_fw", "title": "Firewalls & ACLs", "prompt": "How do firewalls and access control lists work? Show example iptables rules."},
        {"id": "ns_ids", "title": "IDS/IPS Systems", "prompt": "How do IDS and IPS systems detect threats? Compare signature-based vs anomaly-based detection."},
        {"id": "ns_vpn", "title": "VPNs & Segmentation", "prompt": "How do VPNs and network segmentation improve security? Compare different VPN protocols."},
        {"id": "ns_wifi", "title": "Wireless Security", "prompt": "What are the main wireless security protocols and their vulnerabilities? Compare WPA2 vs WPA3."},
    ],
    "Web App Security": [
        {"id": "wa_sqli", "title": "SQL Injection", "prompt": "Explain SQL injection attacks. Show vulnerable code and the secure parameterized version."},
        {"id": "wa_xss", "title": "Cross-Site Scripting (XSS)", "prompt": "Explain the three types of XSS (stored, reflected, DOM-based) with code examples."},
        {"id": "wa_csrf", "title": "CSRF & SSRF", "prompt": "Explain CSRF and SSRF attacks. How do anti-CSRF tokens work?"},
        {"id": "wa_auth", "title": "Authentication Flaws", "prompt": "What are common authentication vulnerabilities? Cover session management, JWT flaws, and credential stuffing."},
        {"id": "wa_headers", "title": "Security Headers & CSP", "prompt": "What HTTP security headers should every web app set? Explain CSP, HSTS, and X-Frame-Options."},
    ],
    "Cloud Security": [
        {"id": "cs_srm", "title": "Shared Responsibility Model", "prompt": "Explain the cloud Shared Responsibility Model. What does the provider secure vs. the customer?"},
        {"id": "cs_iam", "title": "IAM & Access Control", "prompt": "How do cloud IAM policies work? Show an example least-privilege AWS IAM policy in JSON."},
        {"id": "cs_storage", "title": "Storage Security (S3)", "prompt": "How do you secure cloud storage like S3 buckets? Cover bucket policies, encryption, and access logging."},
        {"id": "cs_iac", "title": "Infrastructure as Code Security", "prompt": "What is IaC security scanning? How do tools like Checkov and tfsec prevent misconfigurations?"},
        {"id": "cs_monitor", "title": "Cloud Monitoring & Logging", "prompt": "How do you set up security monitoring in the cloud? Cover CloudTrail, GuardDuty, and SIEM integration."},
    ],
    "Cryptography": [
        {"id": "cr_symm", "title": "Symmetric vs Asymmetric", "prompt": "Compare symmetric and asymmetric encryption. When do you use each? Give algorithm examples."},
        {"id": "cr_hash", "title": "Hashing & Password Storage", "prompt": "Explain the difference between encryption and hashing. Why use bcrypt/Argon2 for passwords instead of SHA-256?"},
        {"id": "cr_tls", "title": "TLS/SSL Protocol", "prompt": "Walk me through the TLS 1.3 handshake step by step. How does it differ from TLS 1.2?"},
        {"id": "cr_sigs", "title": "Digital Signatures & PKI", "prompt": "How do digital signatures and PKI (Public Key Infrastructure) work? Explain certificate chains."},
        {"id": "cr_keys", "title": "Key Management", "prompt": "What are best practices for cryptographic key management? Cover key rotation, HSMs, and key derivation."},
    ],
    "Incident Response": [
        {"id": "ir_prep", "title": "IR Planning & Preparation", "prompt": "What should an incident response plan include? Cover team roles, communication plans, and playbooks."},
        {"id": "ir_detect", "title": "Detection & Analysis", "prompt": "How do you detect and analyze a security incident? Cover log analysis, IOCs, and triage methodology."},
        {"id": "ir_contain", "title": "Containment & Eradication", "prompt": "Explain containment strategies during an incident. When do you isolate vs. monitor?"},
        {"id": "ir_recover", "title": "Recovery & Post-Incident", "prompt": "How do you recover from an incident and conduct a blameless post-mortem?"},
        {"id": "ir_forensics", "title": "Digital Forensics Basics", "prompt": "Explain the basics of digital forensics. Cover evidence collection, chain of custody, and volatile data."},
    ],
}


def render_progress(user_email: str) -> None:
    """Render the progress dashboard."""
    st.markdown("# 📊 Progress Dashboard")

    # ── Quiz scores across domains ────────────────────────────────────────
    quiz_results = db.get_quiz_results(user_email)
    domain_scores: dict[str, dict] = {}
    if quiz_results:
        for r in quiz_results:
            domain_scores[r["domain"]] = r

    st.markdown("## Quiz Scores")
    if not domain_scores:
        st.markdown(
            "<p style='color:var(--text3);font-style:italic'>"
            "No quizzes completed yet. Head to the Quiz tab to test your knowledge!</p>",
            unsafe_allow_html=True,
        )
    else:
        for domain in chat.DOMAINS:
            if domain in domain_scores:
                r = domain_scores[domain]
                pct = r["score"] / r["total"] if r["total"] > 0 else 0
                label = f"{r['score']}/{r['total']}"
            else:
                pct = 0.0
                label = "Not taken"

            st.markdown(
                f"<div class='progress-domain-label'>"
                f"{html_lib.escape(domain)}"
                f"<span class='progress-score-label'>{label}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(pct)

    st.divider()

    # ── Learning Paths ────────────────────────────────────────────────────
    st.markdown("## Learning Paths")
    st.markdown(
        "<p style='color:var(--text2)'>Work through topics in each domain. "
        "Click <strong>Learn</strong> to start a guided chat or <strong>Practice</strong> to test in Lab mode.</p>",
        unsafe_allow_html=True,
    )

    completed = db.get_completed_topics(user_email)
    completed_ids: set[str] = set(completed) if completed else set()

    # Domain tab selector
    domain_tab = st.selectbox(
        "Select domain",
        chat.DOMAINS,
        key="progress_domain_select",
        label_visibility="collapsed",
    )

    topics = LEARNING_PATHS.get(domain_tab, [])
    done_count = sum(1 for t in topics if t["id"] in completed_ids)
    total_count = len(topics)

    st.markdown(
        f"<div class='progress-domain-label'>"
        f"Progress: {done_count}/{total_count} topics"
        f"<span class='progress-score-label'>{done_count * 100 // total_count if total_count else 0}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.progress(done_count / total_count if total_count else 0.0)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    for t in topics:
        is_done = t["id"] in completed_ids
        icon = "✅" if is_done else "⬜"

        col_check, col_title, col_learn, col_practice, col_mark = st.columns([0.5, 4, 1.5, 1.5, 1.5])
        with col_check:
            st.markdown(f"<div style='font-size:1.2rem;padding-top:6px'>{icon}</div>", unsafe_allow_html=True)
        with col_title:
            st.markdown(f"<div style='padding-top:8px'>{html_lib.escape(t['title'])}</div>", unsafe_allow_html=True)
        with col_learn:
            if st.button("📖 Learn", key=f"learn_{t['id']}", use_container_width=True):
                st.session_state.pending_prompt = t["prompt"]
                st.session_state.lab_mode = False
                st.session_state.selected_domain = domain_tab
                st.session_state.active_page = "💬 Chat"
                st.rerun()
        with col_practice:
            if st.button("🧪 Practice", key=f"practice_{t['id']}", use_container_width=True):
                st.session_state.pending_prompt = t["prompt"]
                st.session_state.lab_mode = True
                st.session_state.selected_domain = domain_tab
                st.session_state.active_page = "💬 Chat"
                st.rerun()
        with col_mark:
            if is_done:
                if st.button("↩ Undo", key=f"undo_{t['id']}", use_container_width=True):
                    db.remove_topic_completion(user_email, t["id"])
                    st.rerun()
            else:
                if st.button("✓ Done", key=f"done_{t['id']}", use_container_width=True):
                    db.save_topic_completion(user_email, domain_tab, t["id"])
                    st.rerun()

    st.divider()

    # ── Session stats ─────────────────────────────────────────────────────
    st.markdown("## Activity Summary")
    total_msgs = st.session_state.get("total_interactions", 0)
    total_convos = len(st.session_state.get("conversation_summaries", []))
    total_quizzes = len(domain_scores)
    total_topics = len(completed_ids)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{total_convos}</div><div class='stat-label'>Conversations</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{total_msgs}</div><div class='stat-label'>Messages Sent</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{total_quizzes}/6</div><div class='stat-label'>Quizzes Done</div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{total_topics}/30</div><div class='stat-label'>Topics Completed</div></div>",
            unsafe_allow_html=True,
        )
