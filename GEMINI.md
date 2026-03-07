# GEMINI.md - Koba_Agents Project Overview

Koba_Agents is a full-stack AI agent application designed to provide a chat interface for managing Google Workspace services, including Gmail, Calendar, Tasks, and Google Drive. It leverages a supervisor agent pattern with LangGraph to delegate tasks to specialized sub-agents, all powered by Google Gemini LLMs.

## Tech Stack

### Backend
- **Language:** Python 3.13
- **Framework:** FastAPI
- **Orchestration:** LangGraph + LangChain
- **LLM:** Google Gemini (selectable models: 2.0 Flash, 2.5 Flash, 2.5 Pro, 3.0 Flash, 3.0 Pro)
- **Database:** PostgreSQL (Supabase) with `AsyncPostgresSaver` for LangGraph check-pointing.
- **Caching:** Redis for token caching, rate limiting, and WebSocket tickets.
- **Background Jobs:** APScheduler for Gmail watch renewal, Google Cloud Tasks for auto-reply processing.

### Frontend
- **Framework:** React 19 + Vite 7
- **Styling:** Tailwind CSS 4
- **Auth:** Supabase Auth with Google OAuth.
- **State Management:** React Context (AuthContext) and Custom Hooks (useChat, useAuth).
- **Communication:** WebSockets for real-time chat and streaming agent responses.

## Getting Started

### Prerequisites
- Python 3.13+
- Node.js 20+
- Supabase account and project
- Redis instance
- Google Cloud Project with Gmail, Calendar, Tasks, and Drive APIs enabled.
- Gemini API Key

### Backend Setup
1. Navigate to the `backend/` directory.
2. Create a `.env` file based on the environment variables listed below.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   python run_app.py
   ```
   Or using uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Navigate to the `frontend/` directory.
2. Create a `.env.local` file with the required VITE_ variables.
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Architecture

### Agent System (`backend/agents/`)
- **SupervisorAgent**: The central coordinator that receives user messages and routes them to the appropriate specialized agent or tool.
- **Specialized Agents**: GmailAgent, CalendarAgent, TasksAgent, and DriveAgent. These inherit from a `BaseAgent` and are exposed as tools to the Supervisor.
- **Tool Strategy**: Each agent is converted to a tool using `agent_to_tool()`, allowing the Supervisor to call them with specific instructions.

### Auto-Reply System
- **Gmail Pub/Sub**: Triggers notifications to a webhook (`POST /webhooks/gmail`).
- **Processing Pipeline**: Webhooks dispatch to Cloud Tasks, which calls `POST /internal/auto-reply/process`.
- **AI Logic**: The processing pipeline uses the `SupervisorAgent` with a compiled set of user-defined rules to decide whether to reply, skip, or perform other actions.

### Data Flow
1. **Chat**: Frontend requests a ticket -> Connects via WebSocket -> Messages are processed by LangGraph -> Responses stream back to the UI.
2. **Auth**: Supabase handles user auth -> Google OAuth credentials are encrypted and stored in Supabase -> Retrieved and cached in Redis when needed for API calls.

## Development Conventions

- **Agent Development**: New agents should inherit from `BaseAgent` and include a `system_prompt.txt`.
- **API Routes**: Grouped by functionality in `backend/routes/`.
- **Frontend Components**: Modularized in `frontend/src/components/`, with logic separated into hooks.
- **Testing**: Frontend tests use Vitest and React Testing Library (`frontend/src/App.test.jsx`).

## Key Files & Directories

- `backend/main.py`: Entry point for the FastAPI application.
- `backend/agents/supervisor.py`: Main agent logic and tool registration.
- `backend/core/db.py`: Database connection and LangGraph check-pointer setup.
- `backend/config.py`: Centralized configuration and environment variable validation.
- `frontend/src/App.jsx`: Main application structure and routing.
- `frontend/src/hooks/useChat.js`: WebSocket and chat history management.
- `CLAUDE.md`: Additional technical guidance for AI assistants.

## Environment Variables

### Backend (`.env`)
- `GOOGLE_API_KEY`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- `SECRET_KEY`, `SECRET_KEY_SALT`
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_DB_URL`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`
- `PUBSUB_TOPIC`, `PUBSUB_WEBHOOK_TOKEN`

### Frontend (`.env.local`)
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- `VITE_BACKEND_URL`, `VITE_WEBSOCKET_URL`
