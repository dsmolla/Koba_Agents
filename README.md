# Koba Agents

Koba Agents is a full-stack, AI-powered assistant designed to seamlessly integrate with and automate your Google Workspace. Utilizing advanced Large Language Models (LLMs) and Google's Generative AI, it acts as a centralized "Supervisor" capable of orchestrating specialized sub-agents to manage emails, calendar events, drive files, documents, sheets, and tasks.

## Features

- **Supervisor Agent Architecture**: Leverages LangGraph/Langchain to route user requests intelligently to the most appropriate specialized Workspace agents.
- **Comprehensive Workspace Integration**:
  - **Gmail**: Read, draft, and send emails. Includes background auto-reply capabilities via webhooks.
  - **Calendar**: Manage your schedule, create events, and check availability.
  - **Docs & Sheets**: Read, edit, and analyze Google Documents and Spreadsheets.
  - **Drive**: Search, organize, and manage files in Google Drive.
  - **Tasks**: Track and manage Google Tasks.
- **Adaptive Memory Management**: Learns from interactions to securely store and retrieve user preferences, context, and configurations.
- **Real-time Gmail Webhooks**: Integrates with Google Cloud Pub/Sub and Cloud Tasks to process incoming emails entirely in the background.
- **Robust Security**: Employs industry-standard OAuth2 flows, token encryption, and Supabase integration for strict access control and Row Level Security.
- **Rate Limiting & Caching**: Utilizes Redis for high-performance dependency caching and robust API rate limits.
- **Modern UI**: A responsive, interactive chat and dashboard interface built with React, Vite, and Tailwind CSS.

---

## Gmail Auto-Reply System

Koba Agents includes a rule-based auto-reply system for your Gmail inbox, completely running in the background.

- **Smart Rules**: Create customizable rules that define "When" an email arrives (conditions) and "Do" (the action to take).
- **Tone Control**: Tailor the tone of the AI's response (e.g., Professional, Casual, Urgent) for each specific rule.
- **Priority Sorting**: Reorder rules to ensure the most important conditions are evaluated first.
- **Push Notifications**: Leverages Google Cloud Pub/Sub to listen to Gmail push notifications (Watch status), processing emails instantly without polling.
- **Audit Logs**: A built-in logging system tracks every autoreply processed, along with timestamps, status, subjects, and the LLM used.

---

## System Architecture

The application is split into two primary components:

### Backend (Python/FastAPI)
The central intelligence repository and API gateway.
- **Framework:** FastAPI, Uvicorn
- **AI/LLM framework:** LangChain, LangGraph, Google Generative AI integrations
- **Database / State:** PostgreSQL (Supabase), Langgraph Checkpointer (Postgres/SQLite)
- **Background Tasks:** APScheduler, Google Cloud Pub/Sub, Cloud Tasks
- **Cache / Message Broker:** Redis
- **Authentication:** OAuth2 (Google), JWT

### Frontend (React/Vite)
A modern client layer delivering a smooth user experience.
- **Framework:** React 19, Vite
- **Styling:** TailwindCSS v4, Lucide React (Icons), FontAwesome
- **Data Fetching / Auth:** Supabase JS client
- **Routing:** React Router DOM

---

## Prerequisites

Before setting up the project, ensure you have the following installed and configured:
- **Node.js** (v18+)
- **Python** (3.10+)
- **Redis server** running locally or remotely
- **PostgreSQL / Supabase** project set up
- A **Google Cloud Project** with the following APIs enabled:
  - Gmail API
  - Google Calendar API
  - Google Drive API
  - Google Docs API
  - Google Sheets API
  - Google Tasks API

---

## ⚙️ Setup Instructions

### 1. Backend Setup

Navigate to the `backend` directory:
```bash
cd backend
```

**Create and activate a virtual environment:**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure Environment Variables:**
Copy the example environment file and fill in your credentials.
```bash
cp example.env .env
```
Ensure you populate your `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `SUPABASE_URL`, `SUPABASE_DB_URL`, and `REDIS` configurations.

### 2. Frontend Setup

Navigate to the `frontend` directory:
```bash
cd ../frontend
```

**Install dependencies:**
```bash
npm install
```

**Configure Environment Variables:**
Copy the example environment file and fill in your credentials.
```bash
cp .env.example .env.local
```
You will need to provide the public Supabase keys for the client, and optionally configure your `VITE_INVITE_REQUEST_EMAIL`, `VITE_INVITE_REQUEST_SUBJECT`, and `VITE_INVITE_REQUEST_BODY` to set up the email template sent by users requesting an invitation code.

### 3. Cloud Provider Setup (GCP & Supabase)
For production or fully featured local development (specifically background webhooks and Gmail push notifications), you must configure your Google Cloud project according to the infrastructure setup guide:
- Refer to `backend/Setup.md` for detailed instructions on configuring GCP Pub/Sub Topics, Cloud Tasks Queues, Redis Instances via Google Cloud, and Cloud Run.

---

## 💻 Running the Application Locally

You will need to run both the backend and frontend servers simultaneously.

**Start the Backend Server (from the `backend` directory):**
```bash
# Ensure your virtual environment is active
python run_app.py
```

**Start the Frontend Development Server (from the `frontend` directory):**
```bash
npm run dev
```

Visit the frontend URL (typically `http://localhost:5173`) in your browser to start interacting with your new AI assistant!

---

## 📂 Project Structure

```
Koba_Agents/
├── backend/
│   ├── agents/          # Contains the Supervisor and specialized sub-agents (Gmail, Calendar, etc.)
│   ├── core/            # Core backend utilities (Auth, DB connectors, Redis, Rate Limiting, Models)
│   ├── routes/          # FastAPI endpoints (chat, settings, webhooks, auth, integrations)
│   ├── services/        # Background service logic (Gmail watch renewals, background jobs)
│   ├── main.py          # FastAPI application entrypoint
│   └── Setup.md         # GCP Cloud infrastructure setup instructions
├── frontend/
│   ├── src/             # React application source code (Components, Pages, Hooks)
│   ├── public/          # Static frontend assets
│   ├── package.json     # Node.js dependencies
│   └── vite.config.js   # Vite configuration
└── README.md            # You are here
```

---

## Authentication & Invitation System

The platform has been secured to strictly accept new registrations **exclusively via invitation codes**. Even Google SSO attempts must have an underlying pre-approved invitation code registered to the email address. 

**Generating an Invitation Code:**
As an administrator, you can issue single-use invitation codes safely to your PostgreSQL database by using the bundled helper script.

1. Ensure your backend environment is active and `.env` is configured.
2. Run the generator script with the target user's email:
   ```bash
   python backend/scripts/generate_invite.py targetuser@example.com
   ```
3. Provide the generated UUID code to the user. A single-use verification trigger in the database will burn the code upon a successful sign-up.

---

## Security Notes

- **Token Encryption**: OAuth tokens and user preferences are encrypted at rest using the secret keys specified in your `.env`.
- **Row Level Security (RLS)**: The PostgreSQL database (Supabase) utilizes RLS to ensure users can only ever access their own data, documents, and agent memory.
- **Webhook Validation**: GCP Cloud Tasks and Pub/Sub webhook endpoints require verification tokens to prevent external unauthorized triggering.

## 🤝 Contributing

Contributions are welcome! If you're submitting a bug fix or new feature, please open an issue first to discuss the proposed change. 

Make sure your code aligns with both `eslint` practices for the frontend and standard Python typing/formatting for the backend.
