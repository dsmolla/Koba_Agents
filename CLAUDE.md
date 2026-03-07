# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Koba_Agents is a full-stack AI agent application providing a chat interface for managing Google Workspace services (Gmail, Calendar, Tasks, Google Drive). It uses a supervisor agent pattern with LangGraph to delegate tasks to specialized sub-agents.

## Tech Stack

- **Frontend**: React 19 + Vite 7 + Tailwind CSS 4
- **Backend**: Python 3.13 + FastAPI + LangGraph + LangChain
- **Database**: PostgreSQL (Supabase) with Redis caching
- **Auth**: Supabase Auth with Google OAuth
- **LLM**: Google Gemini (user-selectable: 3.0 Pro, 3.0 Flash, 2.5 Flash, 2.5 Pro)

## Commands

### Frontend (from `frontend/`)
```bash
npm install          # Install dependencies
npm run dev          # Start dev server (port 5173)
npm run build        # Production build
npm run lint         # Run ESLint
npm run test         # Run Vitest tests
```

### Backend (from `backend/`)
```bash
pip install -r requirements.txt
python run_app.py                          # Dev server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000  # Production
```

## Architecture

### Agent System (`backend/agents/`)
- **SupervisorAgent** (`supervisor.py`): Main coordinator that routes requests to specialized agents
- All agents inherit from **BaseAgent** (`common/agent.py`) and expose themselves as tools via `agent_to_tool()`
- **GmailAgent**: Has sub-agents for search/retrieval, organization, summary/analytics, and writing
- **DriveAgent**: Has sub-agents for organization, search/retrieval, and writing
- **CalendarAgent**, **TasksAgent**: Handle respective Google services
- System prompts are in `.txt` files alongside each agent
- **GmailAutoReplyAgent** (`gmail/auto_reply/agent.py`): Special-purpose agent used only in the auto-reply pipeline (not exposed as a tool); takes compiled rules and decides which rule applies or returns "IGNORE". Tools: `GetEmailTool`, `GetThreadDetailsTool`, `ReplyEmailTool`, `DraftEmailTool`, `CurrentDateTimeTool`

#### Agent Hierarchy
```
SupervisorAgent
├── GmailAgent
│   ├── OrganizationAgent      (label management, email deletion)
│   ├── SearchAndRetrievalAgent (email search, retrieval, attachments)
│   ├── SummaryAndAnalyticsAgent (summarization, classification)
│   └── WriterAgent            (send, draft, reply, forward)
├── CalendarAgent
├── DriveAgent
│   ├── OrganizationAgent
│   ├── SearchAndRetrievalAgent
│   └── WriterAgent
└── TasksAgent

GmailAutoReplyAgent            (auto-reply pipeline only)
```

#### Common Tools (`agents/common/`)
- `tools.py` — **CurrentDateTimeTool**: Returns current date/time in user's timezone; **BaseGoogleTool**: Abstract base catching `ProviderNotConnectedError`, `RefreshError`, `HttpError` and returning user-friendly messages
- `download_supabase_to_disk.py` — Helper used by agents to download Supabase-hosted files to local disk for processing

### App Entry Point (`backend/main.py`)
- App wiring only: lifespan, middleware, exception handler, router includes
- `app.state.agents`: Dict of `model_name -> SupervisorAgent` (cached per model)
- `app.state.checkpointer`: Shared PostgreSQL checkpointer
- `get_agent(app, model_name)`: Returns cached agent or creates a new one; falls back to `DEFAULT_MODEL` if model name is invalid
- Lifespan: connects DB + creates checkpointer + **pre-creates the default model agent** + starts APScheduler on startup; shuts down scheduler + disconnects DB on shutdown (subsequent models are created lazily on first use)
- **googleapiclient cache patch**: On startup, patches the `googleapiclient` discovery cache to `_MemoryCache` to avoid disk writes and redundant network fetches on every API call

### Logging (`backend/logging_config.py`)
- **Dual output**: Console (ANSI colors, human-readable) + rotating JSON file (10MB per file, 5 backups)
- **SensitiveDataFilter**: Applied to both handlers — redacts OAuth tokens, API keys, Bearer tokens, passwords, email addresses, and long base64-like strings
- **CustomJsonFormatter**: Adds contextual fields to JSON logs: timestamp, level, logger, user_id, session_id, agent_name, tool_name, execution_time
- **`log_event()`**: Logs LangGraph stream events (`on_chain_start`, `on_tool_start`, `on_tool_end`, `on_chat_model_end`); called conditionally at DEBUG level in `chat.py`

### Routes (`backend/routes/`)
- `auth.py`: `POST /auth/ticket` — WebSocket ticket generation
- `chat.py`: `WS /ws/chat` + `DELETE /chat/clear` — WebSocket handler with `send_chat_history()` and `process_message()` helpers
- `health.py`: `GET /health` — deep health check (pings PostgreSQL + Redis, returns 200/503)
- `integrations.py`: `POST/GET/DELETE /integrations/*` — Google OAuth credential management
- `models.py`: `GET /models` — returns available LLM models and default
- `auto_reply.py`: `/auto-reply/rules` CRUD, `/auto-reply/rules/reorder`, `/auto-reply/rules/{id}/toggle`, `/auto-reply/watch`, `/auto-reply/watch/toggle`, `/auto-reply/log`
- `settings.py`: `GET/PUT /settings` — user timezone (validated against `zoneinfo.available_timezones()`)
- `webhooks.py`: `POST /webhooks/gmail` — Gmail Pub/Sub push notifications
- `internal.py`: `POST /internal/gmail/auto-reply/process` — Cloud Tasks target endpoint (OIDC + `X-Cloud-Tasks-Token` header auth)

### Services (`backend/services/`)
- `auto_reply.py`: Email processing pipeline — rule matching, AI reply generation via GmailAutoReplyAgent, rate limiting, loop prevention. Key functions: `should_skip_email() -> tuple[bool, str|None]` (returns skip flag + subject), `check_rate_limit()`, `log_auto_reply()`, `process_notification()`
- `gmail_watch.py`: Gmail Pub/Sub watch lifecycle (start, stop, renew). APScheduler renews watches every 6 hours via `renew_all_watches()`. Also provides `get_history_changes()` for fetching new messages
- `cloud_tasks.py`: Google Cloud Tasks enqueue helper with dedup via task name (`enqueue_notification_task()`)

### Core Backend (`backend/core/`)
- `db.py`: PostgreSQL connection pool, LangGraph AsyncPostgresSaver, `get_user_timezone()`, `set_user_timezone()`, `pubsub_notification_exists()`, `transaction()` context manager
- `redis_client.py`: Token caching (1hr expiry), WebSocket tickets (30s TTL), rate limiting sliding window
- `auth.py`: Google service getters (`get_google_service()`, `get_gmail_service()`, `get_calendar_service()`, `get_drive_service()`, `get_tasks_service()`) that retrieve `api_service` from LangGraph config
- `rate_limit.py`: `RateLimitMiddleware` (HTTP) and `check_ws_rate_limit()` (WebSocket), Redis-backed sliding window
- `dependencies.py`: FastAPI dependency injection — `get_current_user_http` (Supabase Bearer token), `get_current_user_ws` (WebSocket ticket), `verify_google_token` (Google OIDC)
- `cache.py`: `EmailCache` — LRU in-memory cache (max 1000 emails) per user keyed by `thread_id` from config; `get_email_cache(config)` helper
- `exceptions.py`: `ProviderNotConnectedError`, `TokenExpiredError`
- `models.py`: Pydantic models — `FileAttachment`, `UserMessage`, `BotMessage`, `GoogleCredentials`
- `supabase_client.py`: Async Supabase singleton; `download_from_supabase()`, `upload_to_supabase()`
- `token_encryption.py`: Fernet (AES-128-CBC) with PBKDF2 key derivation (480,000 iterations); `encrypt(token: dict)`, `decrypt(encrypted_token: str)`

### Frontend Structure (`frontend/src/`)
- `hooks/useChat.js`: WebSocket connection, message history, file uploads, rate-limit feedback; persists selected model to `localStorage`
- `hooks/useAuth.js`: Auth state from Supabase via `AuthContext`
- `context/AuthContext.jsx`: Session state, Google integration status (`googleIntegration`, `fetchGoogleIntegration`)
- `lib/supabase.js`: Supabase client + auth helpers (`signInUser`, `signUpUser`, `signOutUser`, `signInWithGoogleProvider`, etc.)
- `lib/fileService.js`: File upload/download/delete/list helpers using Supabase Storage
- `assets/icons.jsx`: Custom SVG icon components — `GoogleDriveIcon`, `GmailIcon`, `GoogleCalendarIcon`, `GoogleTasksIcon` (accept `size` and `className` props)
- `components/dashboard/ChatView.jsx`: Main chat interface — message history with markdown rendering (`react-markdown`), streaming, file uploads, file reference autocomplete (`@filename`), model selector (fetches from `/models`, persists to `localStorage`)
- `components/dashboard/TaskManager.jsx`: Google Tasks management UI; also renders `AutoReplySection` when Gmail is connected
- `components/dashboard/AutoReplySection.jsx`: Rules list with drag-and-drop reorder (`@dnd-kit`), per-rule enable/disable toggle, watch toggle button, and auto-reply activity log viewer (last 50 entries)
- `components/dashboard/AutoReplyRuleModal.jsx`: Rule create/edit modal with When/Do/Tone fields
- `components/dashboard/FileManager.jsx`: Supabase Storage file upload/download/delete interface
- `components/dashboard/SettingsView.jsx`: Profile editing, Google integration connect/disconnect per service, timezone selector, sign-out
- `components/dashboard/Sidebar.jsx`: Collapsible navigation between dashboard views; user profile button at bottom
- `components/auth/`: `AuthInput`, `AuthLayout`, `GoogleSignInButton`
- `components/ProtectedRoute.jsx`, `AuthRoute.jsx`, `ErrorBoundary.jsx`, `ErrorAlert.jsx`
- `pages/Dashboard.jsx`: Main dashboard container with tab-based navigation (chat, files, tasks, settings)
- `pages/auth/`: Login, Signup, ResetPassword, UpdatePassword

**Key frontend libraries**: `react-markdown` (bot message rendering), `react-hot-toast` (toast notifications in AutoReplySection/SettingsView), `lucide-react` (icons), `@dnd-kit` (drag-and-drop rule reordering)

### WebSocket Flow
1. Frontend requests one-time ticket via `POST /auth/ticket`
2. Connects to `WS /ws/chat?ticket=<ticket>&timezone=<tz>`
3. Backend validates ticket, establishes connection
4. Per message: `APIServiceLayer` created once and passed via `RunnableConfig.configurable['api_service']`
5. All tools in that message retrieve the service from config (no repeated Redis/DB lookups)
6. Messages stream through LangGraph supervisor with status updates

### Rate Limiting
- **HTTP**: 60 requests/minute per user (or IP if unauthenticated) — skips WebSocket upgrades, /docs, /openapi.json, /health, /webhooks/*, /internal/*
- **WebSocket**: 10 messages/minute per user
- Configured in `core/rate_limit.py`, uses Redis sliding window

### Key API Endpoints
```
POST   /auth/ticket                       # Get WebSocket ticket
POST   /integrations/google               # Save Google OAuth credentials
GET    /integrations/{provider}           # Check integration status
DELETE /integrations/{provider}           # Revoke integration
DELETE /chat/clear                        # Clear chat history
GET    /health                            # Deep health check (PostgreSQL + Redis)
GET    /models                            # Available LLM models + default
WS     /ws/chat                           # Main chat endpoint
GET    /settings                          # User settings (timezone)
PUT    /settings                          # Update user settings
GET    /auto-reply/watch                  # Get Gmail watch status (is_active)
POST   /auto-reply/watch/toggle           # Start or stop Gmail watch
POST   /auto-reply/rules                  # Create auto-reply rule
GET    /auto-reply/rules                  # List rules (ordered by priority)
GET    /auto-reply/rules/{id}             # Get specific rule
PUT    /auto-reply/rules/{id}             # Update rule
DELETE /auto-reply/rules/{id}             # Delete rule
PATCH  /auto-reply/rules/{id}/toggle      # Enable/disable rule
POST   /auto-reply/rules/reorder          # Reorder rule priority (drag-and-drop)
GET    /auto-reply/log                    # Auto-reply activity log (last 50)
POST   /webhooks/gmail                    # Gmail Pub/Sub push notification receiver
POST   /internal/gmail/auto-reply/process # Cloud Tasks processing endpoint
```

### Model Selection
- Users select a Gemini model from a dropdown in the chat input area
- Frontend fetches available models from `GET /models` on mount, persists selection to `localStorage`
- Each message includes the selected model ID; backend resolves the correct `SupervisorAgent` via `get_agent()`
- The default model agent is pre-created on startup; other model agents are lazily created on first use and cached in `app.state.agents`
- Configured in `config.py`: `ALLOWED_MODELS` (dict of ID → display name), `DEFAULT_MODEL`

### Caching Strategy
- **Google tokens**: Redis (1hr TTL) → PostgreSQL (persistent, encrypted with Fernet/PBKDF2)
- **API service per message**: Created in `routes/chat.py`, passed via LangGraph config to avoid repeated lookups
- **Agent instances**: Cached per model in `app.state.agents` (lazy initialization)
- **Email cache**: In-memory LRU per user (`core/cache.py`), keyed by `config['configurable']['thread_id']`

### Auto-Reply System
AI-powered email auto-reply triggered by Gmail Pub/Sub notifications:
1. **Gmail Pub/Sub** sends push notification to `POST /webhooks/gmail`
2. **Webhook** deduplicates via `pubsub_notifications` table, dispatches to **Cloud Tasks** (production) or **BackgroundTasks** (local dev fallback)
3. **Cloud Tasks** calls `POST /internal/gmail/auto-reply/process` with OIDC token + `X-Cloud-Tasks-Token` header
4. **Processing pipeline** (`services/auto_reply.py`):
   - Fetches new messages via Gmail history API
   - 6-layer loop prevention: DB dedup, own-email filter, SENT/DRAFT/SPAM/TRASH/CATEGORY_PROMOTIONS labels, noreply sender detection, auto-generated email headers (Auto-Submitted, X-Autoreply, X-Auto-Response-Suppress, Precedence), hourly rate limit
   - Compiles all enabled rules into a system prompt (in `sort_order` priority)
   - Calls **GmailAutoReplyAgent** with the compiled prompt — agent reads the email, decides which rule applies, and executes the action directly using its tools (reply, Drive, Calendar, etc.)
   - If agent responds "IGNORE", nothing is logged (no rule matched)
   - Otherwise logs to `auto_reply_log` with status (sent/failed)
- Rules have three natural-language fields: `when_condition` (trigger), `do_action` (what to do), `tone` (Professional/Casual/Brief)
- Gmail watch is **manually toggled** by the user via `POST /auto-reply/watch/toggle` — not auto-started/stopped by rule CRUD
- Gmail watch lifecycle managed by `services/gmail_watch.py` (renews every 6h via APScheduler)

### Database Tables
- `public.user_integrations` — OAuth tokens (user_id, provider, credentials [encrypted], updated_at)
- `public.user_settings` — User preferences (user_id, timezone, updated_at)
- `public.gmail_watch_state` — Gmail Pub/Sub watch state (user_id, email, history_id, watch_expiration, is_active)
- `public.auto_reply_rules` — Auto-reply rules (id, user_id, name, when_condition, do_action, tone, sort_order, is_enabled)
- `public.auto_reply_log` — Activity log (id, user_id, message_id, reply_message_id, status, error_message, llm_model, subject)
- `public.pubsub_notifications` — Pub/Sub dedup (message_id, email, history_id)
- LangGraph tables — Managed automatically by `AsyncPostgresSaver`

**Migrations** (`backend/migrations/001_performance_indexes.sql`):
- `idx_auto_reply_log_user_replied_at` on `(user_id, replied_at DESC)` — for `/auto-reply/log` queries
- `idx_auto_reply_log_user_message` on `(user_id, message_id)` — for auto-reply dedup
- `idx_gmail_watch_email_active` on `(email) WHERE is_active = TRUE` — for webhook email lookups
- `idx_auto_reply_rules_user_enabled_order` on `(user_id, sort_order) WHERE is_enabled = TRUE` — for rule fetching
- Also normalizes `gmail_watch_state.email` to lowercase for consistent lookups

### Error Handling
- Gemini API errors (503, rate limits) are caught in the WebSocket handler and sent to the client as `MODEL_ERROR` instead of crashing the connection
- Google auth errors (`ProviderNotConnectedError`, `TokenExpiredError`) sent as `AUTH_REQUIRED` / `AUTH_EXPIRED`

## Adding a New Agent

1. Create directory in `backend/agents/` (e.g., `agents/new_service/`)
2. Create agent class inheriting from `BaseAgent` (`agents/common/agent.py`)
3. Add `system_prompt.txt` for the agent's instructions
4. Register in `SupervisorAgent` (`supervisor.py`)

## Environment Variables

### Backend (`.env`)
- `GOOGLE_API_KEY`: Gemini API key
- `GOOGLE_OAUTH_CLIENT_ID/SECRET`: OAuth credentials
- `SECRET_KEY`, `SECRET_KEY_SALT`: Token encryption (PBKDF2 key derivation)
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_DB_URL`: Database
- `SUPABASE_USER_FILE_BUCKET`: Supabase Storage bucket name for user file uploads
- `REDIS_HOST/PORT/USERNAME/PASSWORD`: Cache
- `PUBSUB_TOPIC`: Gmail watch Pub/Sub topic name
- `PUBSUB_WEBHOOK_TOKEN`: Webhook validation token
- `AUTO_REPLY_HOURLY_LIMIT`: Max auto-replies per user per hour (default 20)
- `CLOUD_TASKS_PROJECT`: GCP project ID for Cloud Tasks
- `CLOUD_TASKS_LOCATION`: Cloud Tasks region (e.g. us-central1)
- `CLOUD_TASKS_QUEUE_NAME`: Cloud Tasks queue name
- `CLOUD_TASKS_SERVICE_ACCOUNT_EMAIL`: Service account used for OIDC token auth
- `CLOUD_TASKS_TOKEN`: Shared secret for internal endpoint auth
- `BASE_PROJECT_URL`: Base URL for Cloud Tasks HTTP target callbacks
- `DEFAULT_MODEL`: Default Gemini model ID (default: gemini-2.5-flash)
- `LOG_LEVEL`: Logging level (default: INFO)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: localhost:5173, localhost:8000)

### Frontend (`.env.local`)
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- `VITE_SUPABASE_USER_FILE_BUCKET`: Supabase Storage bucket name (used by `fileService.js`)
- `VITE_BACKEND_URL`: API URL (defaults to localhost:8000)
- `VITE_WEBSOCKET_URL`: WebSocket URL
