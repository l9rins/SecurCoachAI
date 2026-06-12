# 🛡️ SecurCoach AI

![SecurCoach AI Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=300&section=header&text=SecurCoach%20AI&fontSize=70&animation=fadeIn&fontAlignY=38&desc=Upgraded%20Cybersecurity%20Training%20Coach%20(RAG%20+%20Agent)&descAlignY=51&descSize=20)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat-square&logo=meta&logoColor=white)](https://console.groq.com)

**[Report Bug](#) • [Request Feature](#)**

</div>

---

## 🚀 Overview

**SecurCoach AI** is a full-stack cybersecurity learning platform that pairs a clean React authentication UI with a Streamlit AI chat dashboard. Users sign in via Supabase Auth, then get dropped into an interactive chat powered by **Llama 3.3 70B via Groq** — with streaming responses, persistent conversation history, AI-generated conversation titles, and domain-specific coaching across six security disciplines.

**🎉 Course Final Upgrade:** The application now includes Retrieval-Augmented Generation (RAG) via a lightweight local vector store, a minimal agentic loop that safely calls a `search_docs` tool, and robust prompt-hijack defenses.

> "An AI-powered cybersecurity training coach — learn security concepts through real, streaming conversations."

---

## ✨ New Upgrades (Course Final)

*   **Retrieval-Augmented Generation (RAG):** Implemented via a lightweight local vector store using `sentence-transformers` and `numpy`.
*   **Minimal Agentic Loop:** Enables the model to call a safe, read-only `search_docs` tool backed by the RAG store.
*   **Prompt-Hijack Defenses:** Robust input sanitization implemented to prevent prompt injection and XSS.
*   **Langfuse Integration:** Built-in (but optional) prompt tracing and observability.

---

## 🌟 Core Features

### 🔐 Authentication
*   Email + password signup with full client-side validation and strength enforcement.
*   Server-side JWT signature verification via PyJWT; no plain-text email bypass.
*   Password reset and email confirmation flows fully integrated.

### 💬 Chat Dashboard
*   **Six Security Domains:** General, Network, Web App, Cloud, Cryptography, and Incident Response.
*   **Streaming Responses:** Text appears token-by-token.
*   **Persistent History:** Chats stored in Supabase with AI-generated titles.
*   **Multi-Model Selector:** Choose between Llama 3.3 70B, Llama 3.1 8B, and Mixtral 8x7B.

### 🧪 Hands-On Lab Mode
*   Toggle Lab Mode to switch from Q&A to hands-on security challenges.
*   AI presents realistic vulnerable code, configs, or logs for you to identify and remediate.
*   Evaluates responses and provides hints without revealing the answer upfront.

### 📝 Skill Assessment & Progress
*   **Quiz Mode:** 30 verified cybersecurity questions with instant grading and explanations.
*   **Progress Dashboard:** Track scores, completed learning paths, and activity stats.

---

## 🏗️ Architecture

```text
User → React Login → Supabase Auth → JWT → Streamlit Dashboard → Groq AI (Llama 3.3)
                                              ↕
                                        Supabase DB
                                     (chat history, profiles)
```

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19 + Supabase JS SDK | Authentication UI (login, signup, validation) |
| **Backend** | Streamlit 1.35+ | AI chat dashboard, session management |
| **Database** | Supabase (PostgreSQL) | User profiles, conversation history |
| **AI** | Llama 3.3 70B (via Groq) | Streaming cybersecurity coaching responses |
| **Auth** | Supabase Auth + PyJWT | JWT-based, verified server-side |

---

## 📂 Project Structure

```text
SecurCoachAI/
├── react-app/                   # React frontend
│   ├── src/                     # React source files (App.js, layout, validation)
│   └── .env.example             # React environment template
├── streamlit/                   # Streamlit backend
│   ├── app.py                   # Main dashboard (UI, chat loop, sanitization)
│   ├── auth.py                  # JWT verification & session helpers
│   ├── chat.py                  # Groq client, streaming, lab mode
│   ├── rag.py                   # Vector store (sentence-transformers & numpy)
│   ├── llm_engine.py            # Retrieval integration, sanitization, agent loop
│   ├── observability.py         # Optional Langfuse tracing wrapper
│   └── ...                      # DB, quiz, progress, config modules
├── .streamlit/
│   └── secrets.toml.example     # Streamlit secrets template
└── requirements.txt             # Python dependencies
```

---

## 🛠️ Setup Instructions

### Prerequisites
*   **Python 3.10+** and **Node.js 18+**
*   **Supabase project** and **Groq API key**

### 1. Quick Start (Local)

Create a virtual environment and install dependencies:
```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Start the React Frontend:
```bash
cd react-app
npm install
npm start
# Running at http://localhost:3000
```

Start the Streamlit Backend:
```bash
# In a new terminal
python -m streamlit run streamlit/app.py
# Running at http://localhost:8501
```

> **Note:** Always navigate to **http://localhost:3000** to log in first. The auth token is passed to Streamlit automatically.

### 2. Configuration

**React Environment (`react-app/.env`)**
```env
REACT_APP_SUPABASE_URL=https://your-project-ref.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
REACT_APP_SUPABASE_USERS_TABLE=users
REACT_APP_STREAMLIT_URL=http://localhost:8501
```

**Streamlit Secrets (`.streamlit/secrets.toml`)**
```toml
GROQ_API_KEY                = "gsk_..."
SUPABASE_URL                = "https://your-project-ref.supabase.co"
SUPABASE_KEY                = "your-service-role-key" 
SUPABASE_JWT_SECRET         = "your-jwt-secret"
REACT_APP_URL               = "http://localhost:3000"
SUPABASE_CHAT_HISTORY_TABLE = "chat_history"
```

---

## 🗄️ Supabase Database Setup

You must set up the following tables in your Supabase SQL Editor. *(See full queries in original docs if needed)*.
*   `users` - Stores public profile data.
*   `chat_history` - Stores every message across all conversations.
*   `quiz_results` - Stores best quiz score per user per domain.
*   `completed_topics` - Tracks learning path completions.

*Note: Streamlit connects using the **service role key** and filters queries server-side, bypassing RLS safely.*

---

## 🔒 Security & Defenses

*   **Input Sanitization:** All user inputs are sanitized with `sanitize_input()` to remove common injection patterns.
*   **Safe Agent Tooling:** The agent only supports a single safe tool (`search_docs`) which is read-only. No arbitrary code execution.
*   **HTML Escaping:** User content is HTML-escaped in the UI.
*   **JWT Verification:** PyJWT verifies signatures; invalid tokens are rejected. No plain-text email bypass.

---

## 👁️‍🗨️ Langfuse Prompt Tracing (Optional)

Langfuse integration is built-in. To enable, add these to your `.streamlit/secrets.toml`:

```toml
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

*Traces base chat requests, agent passes, and tool calls (`tool:search_docs`).*

---

## 🧪 Testing Checklist

- [ ] Install dependencies and run the app locally.
- [ ] Enable RAG (Sidebar > Advanced Settings) and upload sample docs (`.txt` or `.md`).
- [ ] Query content in uploaded docs and confirm grounded passages appear in the context.
- [ ] Enable agent mode, instruct the assistant to call `search_docs`, and confirm it returns a grounded final answer.

---

## 📦 Deliverables & Next Steps

### Required Deliverables:
1.  **Presentation Slides:** Use `PRESENTATION_SLIDES.md` or request automated generation.
2.  **Public GitHub Repo:** Push workspace to a public repository.
3.  **App Deployment:** Deploy on Streamlit Cloud and include the link.

### Optional Next Steps (I can help with):
-   Run automated unit smoke tests.
-   Configure Langfuse integrations fully.
-   Create a `.pptx` slide deck programmatically (requires `python-pptx`).

---

## 💡 Known Gotchas

*   **"Check your email" on local signup:** Disable "Confirm email" in Supabase Auth settings for local dev.
*   **Streamlit "Access Denied":** Always start at the React app (`localhost:3000`), not Streamlit.
*   **Groq API limits:** Free tier has strict per-minute rate limits.

---

## 🗺️ Roadmap

- [x] Hands-on lab mode
- [x] Multi-model selector
- [ ] User profile page
- [ ] Difficulty selector adjusts system prompt
- [ ] Admin dashboard

---

<div align="center">

**Built with React, Streamlit, Supabase, and Llama 3.3 70B via Groq**

</div>
