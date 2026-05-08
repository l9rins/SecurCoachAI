<div align="center">

# 🛡️ SecurCoach AI

**An AI-powered cybersecurity training coach — learn security concepts through real, streaming conversations.**

> **Note:** This project uses **Groq** (with Llama 3.3 70B) for AI responses, **not** Google Gemini.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat-square&logo=meta&logoColor=white)](https://console.groq.com)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [React Environment Variables](#react--react-appenv)
  - [Streamlit Secrets](#streamlit--streamlitsecretstoml)
  - [Where to Find Each Key](#where-to-find-each-key)
- [Supabase Database Setup](#supabase-database-setup)
  - [users table](#users-table)
  - [chat_history table](#chat_history-table)
  - [A note on RLS and the service role key](#a-note-on-rls-and-the-service-role-key)
- [Running the App](#running-the-app)
- [Features](#features)
- [Security Notes](#security-notes)
- [Known Gotchas](#known-gotchas)
- [Roadmap](#roadmap)

---

## Overview

SecurCoach AI is a full-stack cybersecurity learning platform that pairs a clean React authentication UI with a Streamlit AI chat dashboard. Users sign in via Supabase Auth, then get dropped into an interactive chat powered by **Llama 3.3 70B via Groq** — with streaming responses, persistent conversation history, AI-generated conversation titles, and domain-specific coaching across six security disciplines.

```
User → React Login → Supabase Auth → JWT → Streamlit Dashboard → Groq AI (Llama 3.3)
                                              ↕
                                        Supabase DB
                                     (chat history, profiles)
```

---

## Architecture

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19 + Supabase JS SDK | Authentication UI (login, signup, validation) |
| **Backend** | Streamlit 1.35+ | AI chat dashboard, session management |
| **Database** | Supabase (PostgreSQL) | User profiles, conversation history |
| **AI** | Llama 3.3 70B (via Groq) | Streaming cybersecurity coaching responses |
| **Auth** | Supabase Auth + PyJWT | JWT-based, verified server-side |

### How auth flows

1. User logs in on the React app (port 3000)
2. React calls Supabase Auth → gets a signed JWT access token
3. React redirects to Streamlit with `?token=<jwt>` in the URL
4. Streamlit verifies the JWT signature using `SUPABASE_JWT_SECRET` via PyJWT
5. On success, the email is extracted from the token payload and stored in session state
6. All subsequent Supabase queries are filtered server-side by that email

---

## Project Structure

```
SecurCoachAI/
│
├── react-app/                   # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js               # Root — switches between login/signup
│   │   ├── index.js             # React entry point
│   │   └── layout/
│   │       ├── LoginLayout.js   # Login form with validation + loading states
│   │       ├── SignupLayout.js  # Signup form, email confirmation screen
│   │       ├── supabase.js      # Supabase SDK client, signIn, signUp helpers
│   │       ├── validation.js    # Pure validation functions (email, password, etc.)
│   │       └── auth.css         # Dark theme styles for auth UI
│   ├── .env.example             # Copy to .env and fill in your keys
│   └── package.json
│
├── streamlit/                   # Streamlit backend
│   ├── app.py                   # Main dashboard — UI, chat loop, session state
│   ├── auth.py                  # JWT verification, session helpers, auth guard
│   ├── chat.py                  # Groq client, streaming, title generation, lab mode
│   ├── db.py                    # All Supabase REST calls (conversations, messages)
│   └── config.py                # Secrets loader + startup validation
│
├── .streamlit/
│   └── secrets.toml.example     # Copy to secrets.toml and fill in your keys
│
├── .gitignore
├── requirements.txt
├── start-dev.ps1                # Starts both services in separate PowerShell windows
├── start-dev.bat                # Wrapper for start-dev.ps1
└── README.md
```

---

## Prerequisites

Make sure you have all of these before starting:

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **A Supabase project** — free tier works fine — [supabase.com](https://supabase.com)
- **A Groq API key** — free tier works fine — [console.groq.com](https://console.groq.com)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/SecurCoachAI.git
cd SecurCoachAI
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

| Package | Purpose |
|---|---|
| `streamlit>=1.35.0` | Web dashboard framework |
| `groq>=0.9.0` | Groq API client (Llama 3.3 70B) |
| `requests>=2.31.0` | Supabase REST calls from Python |
| `PyJWT[crypto]>=2.8.0` | JWT signature verification |

### 3. Install React dependencies

```bash
cd react-app
npm install
cd ..
```

---

## Configuration

There are **two** config files to create — one for React, one for Streamlit. Neither should ever be committed to git (both are in `.gitignore`).

### React — `react-app/.env`

Copy the example and fill in your values:

```bash
cp react-app/.env.example react-app/.env
```

```env
REACT_APP_SUPABASE_URL=https://your-project-ref.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
REACT_APP_SUPABASE_USERS_TABLE=users
REACT_APP_STREAMLIT_URL=http://localhost:8501
```

> ⚠️ **Only the `anon` key goes here.** This file is bundled into the browser
> build and is publicly visible. Never put the service role key in `.env`.

### Streamlit — `.streamlit/secrets.toml`

Copy the example and fill in your values:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
GROQ_API_KEY                = "gsk_..."
SUPABASE_URL                = "https://your-project-ref.supabase.co"
SUPABASE_KEY                = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # service_role key
SUPABASE_JWT_SECRET         = "your-jwt-secret"
REACT_APP_URL               = "http://localhost:3000"
SUPABASE_CHAT_HISTORY_TABLE = "chat_history"
```

### Where to Find Each Key

| Key | Where to find it |
|---|---|
| `REACT_APP_SUPABASE_URL` | Supabase Dashboard → Project Settings → API → **Project URL** |
| `REACT_APP_SUPABASE_ANON_KEY` | Supabase Dashboard → Project Settings → API → **anon / public** |
| `SUPABASE_KEY` | Supabase Dashboard → Project Settings → API → **service_role / secret** |
| `SUPABASE_JWT_SECRET` | Supabase Dashboard → Project Settings → API → **JWT Secret** |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys → Create |

> 🔐 **`SUPABASE_KEY` is the service role key** — it has full admin access to your
> database and bypasses all Row Level Security. It is safe to use here because
> Streamlit runs as a trusted server process and never exposes this key to the
> browser. The React frontend uses only the `anon` key.

---

## Supabase Database Setup

Open your Supabase project → **SQL Editor** → paste and run each block below.

### `users` table

Stores public profile data for each registered user.

```sql
create table users (
  id         uuid        primary key default gen_random_uuid(),
  email      text        unique not null,
  full_name  text,
  username   text,
  created_at timestamptz default now()
);

-- Enable Row Level Security
alter table users enable row level security;

-- Users can only read, insert, and update their own row
create policy "Users can read own row"
  on users for select
  using (auth.uid() = id);

create policy "Users can insert own row"
  on users for insert
  with check (auth.uid() = id);

create policy "Users can update own row"
  on users for update
  using (auth.uid() = id);
```

### `chat_history` table

Stores every message (user and AI) across all conversations.

```sql
create table chat_history (
  id              uuid        primary key default gen_random_uuid(),
  user_id         text        not null,      -- stores the user's email address
  conversation_id text        not null,      -- UUID grouping messages into threads
  title           text,                      -- AI-generated conversation title
  sender          text        not null,      -- 'user' or 'ai'
  message         text        not null,
  created_at      timestamptz default now()
);

-- Enable Row Level Security
alter table chat_history enable row level security;

-- Users can only access their own messages
create policy "Users see own messages"
  on chat_history for select
  using (user_id = (auth.jwt() ->> 'email'));

create policy "Users insert own messages"
  on chat_history for insert
  with check (user_id = (auth.jwt() ->> 'email'));

create policy "Users update own messages"
  on chat_history for update
  using (user_id = (auth.jwt() ->> 'email'));

create policy "Users delete own messages"
  on chat_history for delete
  using (user_id = (auth.jwt() ->> 'email'));
```

### A note on RLS and the service role key

The Streamlit backend connects using the **service role key**, which bypasses RLS entirely. This is intentional — the backend is a trusted server process that already enforces data isolation by filtering every query with `&user_id=eq.{email}` before it hits the database.

The RLS policies above are still worth creating as a **defence-in-depth** measure. They protect your data if:
- You ever accidentally use the `anon` key on the backend
- You add a client-side feature that queries Supabase directly
- A misconfiguration exposes direct database access

> **Why `(auth.jwt() ->> 'email')` instead of `auth.email()`?**
> The `auth.email()` helper function does not exist in all Supabase
> environments and will throw an SQL syntax error on standard projects.
> The JWT extraction syntax `(auth.jwt() ->> 'email')` works universally.

---

## Running the App

### Option 1 — PowerShell script (Windows, recommended)

Launches both services in separate terminal windows:

```powershell
.\start-dev.ps1
```

Or via the batch file wrapper:

```bat
start-dev.bat
```

### Option 2 — Manual (any OS)

Open two terminals:

**Terminal 1 — Streamlit backend:**
```bash
python -m streamlit run streamlit/app.py
# Running at http://localhost:8501
```

**Terminal 2 — React frontend:**
```bash
cd react-app
npm start
# Running at http://localhost:3000
```

### Then open your browser

Navigate to **http://localhost:3000** — always start from the React login page, not Streamlit directly. The auth token is passed from React to Streamlit on login; opening Streamlit directly will show an "Access Denied" screen.

---

## Features

### Authentication
- ✅ Email + password signup with full client-side validation
- ✅ Password strength enforcement (8+ chars, uppercase, digit, special character)
- ✅ Username format enforcement (3–30 chars, alphanumeric + underscore)
- ✅ Confirm password matching on signup
- ✅ Email confirmation flow (shows "check your inbox" screen when enabled in Supabase)
- ✅ Password reset flow ("Forgot password?" link on login page)
- ✅ Button disabled + spinner during API calls — no double-submits
- ✅ Inline per-field error messages
- ✅ JWT passed securely via query param — no plain-text email bypass
- ✅ Server-side JWT signature verification via PyJWT (fails closed — no fallback decode)
- ✅ Automatic session expiry when JWT expires

### Chat Dashboard
- ✅ Six security domains: General Security, Network Security, Web App Security, Cloud Security, Cryptography, Incident Response
- ✅ Streaming AI responses — text appears token-by-token as Groq generates it
- ✅ Stop generation button — cancel long responses mid-stream
- ✅ Persistent conversation history stored in Supabase
- ✅ AI-generated conversation titles (extracted inline from response — no extra API call)
- ✅ Domain-specific suggested starter questions (shown on empty chat)
- ✅ Conversation search — filter sidebar by title
- ✅ Context truncation warning when conversation exceeds 20 messages
- ✅ Structured AI output format (Answer / Example / Think About This)
- ✅ 2-second rate limit between messages
- ✅ Export any conversation to `.md` file
- ✅ Delete individual conversations
- ✅ Visible DB error banners — errors are never silently swallowed
- ✅ Session stats (elapsed time, message count) in sidebar

### Multi-Model Selector
- ✅ Choose between three Groq models in the sidebar:
  - **Llama 3.3 70B** — Most capable, best for complex topics (default)
  - **Llama 3.1 8B** — Fast, good for quick questions
  - **Mixtral 8x7B** — Balanced, 32K context window
- ✅ Model selection persists across messages within a session

### 🧪 Hands-On Lab Mode
- ✅ Toggle Lab Mode in the sidebar to switch from Q&A to hands-on security challenges
- ✅ The AI presents realistic vulnerable code, configs, or logs and asks you to identify, exploit, and remediate the issue
- ✅ Six domain-specific lab scenarios (OWASP code review, IAM policy audit, firewall config analysis, incident log forensics, crypto implementation review, and general misconfig hunting)
- ✅ The AI evaluates your response and provides hints if incorrect — never reveals the answer upfront
- ✅ Lab-specific suggested challenges shown on empty chat
- ✅ Visual `🧪 Lab` chip badge in the header when active

### Code Quality
- ✅ `app.py` split into four focused modules (`auth`, `db`, `chat`, `config`)
- ✅ Dashboard CSS extracted to external file (`dashboard.css`)
- ✅ Unified design token palette between React auth and Streamlit dashboard
- ✅ Startup config validation — clear error message if any secret is missing
- ✅ Type annotations throughout Python codebase
- ✅ Official `@supabase/supabase-js` SDK in React (replaces ~150 lines of manual `fetch`)

---

## Security Notes

| Risk | Mitigation |
|---|---|
| Forged JWT tokens | PyJWT verifies signature using `SUPABASE_JWT_SECRET` — invalid tokens are rejected |
| Plain-text email auth bypass | Removed — only signed JWTs are accepted |
| JWT signature bypass (dev fallback) | Removed — auth fails closed if PyJWT or the secret is unavailable |
| Expired JWT sessions | JWT `exp` claim re-checked on every page load; expired sessions redirect to login |
| Weak passwords | Requires 8+ chars with uppercase, digit, and special character |
| Cross-user data access | Server-side `user_id` filter on every query + RLS policies as backup |
| Service role key exposure | Lives only in `.streamlit/secrets.toml` — gitignored, never sent to browser |
| Double form submission | Submit button disabled during in-flight API calls |
| Message flooding | 2-second cooldown enforced in session state |

---

## Known Gotchas

**"Check your email" screen appears on signup even locally**
This means Supabase has "Confirm email" enabled. Either disable it in Supabase → Authentication → Providers → Email → toggle off "Confirm email" for local dev, or just confirm the email and then sign in normally.

**Streamlit shows "Access Denied"**
You navigated directly to `http://localhost:8501` without going through the React login first. Always start at `http://localhost:3000`.

**`SUPABASE_JWT_SECRET` — where exactly is it?**
Supabase Dashboard → Project Settings → API → scroll to the bottom → **JWT Settings** → copy the secret. It is not the same as your API keys.

**Groq API quota errors**
The free tier of Groq has per-minute rate limits. If you hit them, wait 60 seconds and try again. For production use, upgrade your Groq plan.

**Conversation titles show raw message text instead of an AI title**
Title generation is async and fires after the first exchange. If the LLM is slow or rate-limited, the title falls back to the first 40 characters of your opening message — this is expected behaviour.

---

## Roadmap

- [x] Password reset flow (`supabase.auth.resetPasswordForEmail`)
- [x] Multi-model selector (Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B)
- [x] Hands-on lab mode — AI presents vulnerable code for user to identify and fix
- [ ] User profile page (update display name, username)
- [ ] Per-domain progress tracking (messages sent, topics covered)
- [ ] Quiz mode — AI generates multiple-choice questions to test retention
- [ ] Difficulty selector (Beginner / Intermediate / Advanced) adjusts system prompt
- [ ] Admin dashboard — user counts, active sessions, error logs
- [ ] Full React SPA — replace Streamlit chat with a React chat component for better mobile support
- [ ] Dedicated `conversations` table — cleaner than parsing `chat_history` rows for summaries

---

<div align="center">
<sub>Built with React, Streamlit, Supabase, and Llama 3.3 70B via Groq</sub>
</div>
