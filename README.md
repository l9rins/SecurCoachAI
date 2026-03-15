# SecurCoach AI

An AI-powered cybersecurity training coach that helps students and professionals learn security concepts through interactive conversations.

## Overview

SecurCoach AI combines a React-based authentication interface with a Streamlit-powered AI chat dashboard. Users authenticate through Supabase and interact with Google's Gemini AI to learn about various cybersecurity domains including network security, web application security, cloud security, cryptography, and incident response.

## Architecture

- **Frontend (React)**: Login/signup interface with Supabase authentication
- **Backend (Streamlit)**: AI chat dashboard with conversation management
- **Database (Supabase)**: User profiles and chat history storage
- **AI (Google Gemini)**: Security coaching responses via Gemini 2.0 Flash models

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Supabase account
- Google AI Studio API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd SecurCoachAI-main
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install React dependencies:
```bash
cd react-app
npm install
cd ..
```

## Configuration

### React Environment Variables

Create `react-app/.env` based on `.env.example`:

```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
REACT_APP_SUPABASE_USERS_TABLE=users
REACT_APP_STREAMLIT_URL=http://localhost:8501
```

### Streamlit Secrets

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-service-key"
SUPABASE_JWT_SECRET = "your-jwt-secret"
REACT_APP_URL = "http://localhost:3000"
```

### Supabase Setup

1. Create a new Supabase project
2. Enable Authentication (Email provider)
3. Create a `users` table with columns:
   - `id` (uuid, primary key)
   - `email` (text, unique)
   - `full_name` (text)
   - `username` (text)
4. Create a `chat_history` table with columns:
   - `id` (uuid, primary key)
   - `user_id` (text)
   - `conversation_id` (text)
   - `sender` (text)
   - `message` (text)
   - `created_at` (timestamp)

## Running the Application

### Option 1: PowerShell Script (Recommended for Windows)

```powershell
.\start-dev.ps1
```

This starts both services in separate windows:
- React app: http://localhost:3000
- Streamlit: http://localhost:8501

### Option 2: Manual Start

Terminal 1 - Streamlit:
```bash
python -m streamlit run streamlit/app.py
```

Terminal 2 - React:
```bash
cd react-app
npm start
```

### Option 3: Batch File (Windows)

```bash
start-dev.bat
```

## Usage

1. Open http://localhost:3000 in your browser
2. Sign up for a new account or log in
3. After successful authentication, you'll be redirected to the Streamlit dashboard
4. Select a security domain from the sidebar
5. Start asking cybersecurity questions to the AI coach

## Features

- **Multi-Domain Training**: General Security, Network Security, Web App Security, Cloud Security, Cryptography, Incident Response
- **AI-Powered Coaching**: Powered by Google Gemini 2.0 Flash
- **Conversation Management**: Save, load, and delete chat histories
- **Secure Authentication**: JWT-based auth via Supabase

## Technologies Used

- **React 19** - Frontend framework
- **Streamlit** - Python web app framework
- **Supabase** - Backend-as-a-Service (auth + database)
- **Google Gemini** - AI language model
- **CSS3** - Custom styling with CSS variables


## Support

For issues or questions, please contact the development team or open an issue in the repository.
