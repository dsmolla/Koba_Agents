# Security TODO — Koba_Agents

> **⚠️ DO FIRST (before any code changes):** `backend/.env` with all production secrets is committed to git.
> Rotate everything now in their respective consoles, then add both `.env` files to `.gitignore`.

---

## OPERATIONAL (no code changes — do these NOW)

- [ ] Rotate `GOOGLE_API_KEY` in Google Cloud Console
- [ ] Rotate `GOOGLE_OAUTH_CLIENT_SECRET`
- [ ] Reset Supabase DB password (update `SUPABASE_DB_URL`)
- [ ] Rotate `REDIS_PASSWORD` in Redis Labs
- [ ] Regenerate `SECRET_KEY` and `SECRET_KEY_SALT`
- [ ] Regenerate `PUBSUB_WEBHOOK_TOKEN`
- [ ] Regenerate `CLOUD_TASKS_TOKEN`
- [ ] Add `backend/.env` and `frontend/.env.local` to `.gitignore`
- [ ] Add `PUBSUB_SERVICE_ACCOUNT_EMAIL` to `backend/.env` and `Config` (needed for CRITICAL-BE-2 below)

---

## CRITICAL

---

### [CRITICAL-BE-1] Timing-Safe Token Comparisons
**Files:** `backend/routes/internal.py:20-23`, `backend/routes/webhooks.py:26-28`

**Problem:** Both endpoints use Python `==` to compare shared-secret tokens. `==` short-circuits on the first byte mismatch, leaking timing information that enables brute-force attacks to guess the token character by character.

- [ ] Fix `backend/routes/internal.py`:
```python
import hmac

# Replace:
if token != Config.CLOUD_TASKS_TOKEN:
    raise HTTPException(status_code=403, detail="Forbidden")

# With:
if not hmac.compare_digest(token or "", Config.CLOUD_TASKS_TOKEN or ""):
    logger.warning("Invalid or missing Cloud Tasks token")
    raise HTTPException(status_code=403, detail="Forbidden")
```

- [ ] Fix `backend/routes/webhooks.py`:
```python
import hmac

# Replace:
if Config.PUBSUB_WEBHOOK_TOKEN and token != Config.PUBSUB_WEBHOOK_TOKEN:
    raise HTTPException(status_code=403, detail="Forbidden")

# With:
if Config.PUBSUB_WEBHOOK_TOKEN and not hmac.compare_digest(token or "", Config.PUBSUB_WEBHOOK_TOKEN):
    logger.warning("Invalid webhook token")
    raise HTTPException(status_code=403, detail="Forbidden")
```

---

### [CRITICAL-BE-2] Google OIDC Token — Missing Audience/Issuer Validation
**File:** `backend/core/dependencies.py:48-59`

**Problem:** `verify_google_token()` verifies the JWT signature but does NOT check `iss` or `aud` claims. Any valid Google OIDC token from *any* Google service (Cloud Run, GCE metadata, etc.) can trigger `/webhooks/gmail`.

- [ ] Fix `backend/core/dependencies.py`:
```python
async def verify_google_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    token = authorization.replace("Bearer ", "")
    try:
        id_info = google_id_token.verify_oauth2_token(
            token, google_requests.Request()
        )
        # Verify issuer
        if id_info.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
            raise ValueError("Unexpected issuer")
        # Verify it's from the expected Pub/Sub service account
        expected_sa = Config.PUBSUB_SERVICE_ACCOUNT_EMAIL  # Add this to Config + .env
        if id_info.get("email") != expected_sa:
            raise ValueError("Unexpected service account email")
    except Exception as e:
        logger.warning(f"OIDC validation failed: {e}")
        raise HTTPException(401, "Invalid OIDC Token")
    return id_info
```

- [ ] Add to `backend/config.py`:
```python
PUBSUB_SERVICE_ACCOUNT_EMAIL = os.getenv("PUBSUB_SERVICE_ACCOUNT_EMAIL", "")
```

- [ ] Add `PUBSUB_SERVICE_ACCOUNT_EMAIL=your-pubsub-sa@your-project.iam.gserviceaccount.com` to `backend/.env`

---

### [CRITICAL-BE-3] CORS Tightening + Security Headers Middleware
**File:** `backend/main.py:77-83`

**Problem:** `allow_methods=["*"]` and `allow_headers=["*"]` are overly permissive. No HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, or Referrer-Policy headers are sent.

- [ ] Fix CORS in `backend/main.py`:
```python
# Replace:
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# With:
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

- [ ] Add `SecurityHeadersMiddleware` to `backend/main.py` (add this BEFORE the CORS middleware):
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
# Then add CORSMiddleware below...
```

---

### [CRITICAL-BE-4] Enable Redis TLS
**File:** `backend/core/redis_client.py:20`

**Problem:** `# ssl=True` is commented out. WebSocket tickets (valid 30s auth tokens) and encrypted OAuth tokens are transmitted in plaintext over the Redis connection.

- [ ] Fix `backend/core/redis_client.py`:
```python
self.redis = Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    username=Config.REDIS_USERNAME,
    password=Config.REDIS_PASSWORD,
    decode_responses=True,
    ssl=True,              # Was commented out — uncomment this line
    max_connections=50,
    socket_timeout=10.0,
    socket_connect_timeout=5.0,
)
```

> **Note:** Verify `REDIS_PORT` is the TLS port (typically 6380 for Redis Labs, not 6379).

---

### [CRITICAL-FE-1] Supabase Session — Use `sessionStorage` Instead of `localStorage`
**File:** `frontend/src/lib/supabase.js`

**Problem:** Supabase defaults to `localStorage` for session persistence. `localStorage` is accessible to any script on the same origin. An XSS vulnerability (e.g., in markdown rendering) can steal the JWT and Google OAuth `provider_token`, giving the attacker full access to the user's Google Workspace.

- [ ] Fix `frontend/src/lib/supabase.js`:
```javascript
// Replace:
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// With:
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
        storage: window.sessionStorage,
        persistSession: true,
        autoRefreshToken: true,
    }
})
```

> `sessionStorage` is tab-isolated and cleared on tab close. Sessions survive page refreshes within the same tab but require re-login on new tabs — appropriate for a sensitive app.

---

### [CRITICAL-FE-2] Replace `localStorage` OAuth Integration Flag with `sessionStorage`
**Files:** `frontend/src/context/AuthContext.jsx:36-38, 66, 86`, `frontend/src/components/dashboard/SettingsView.jsx:116`

**Problem:** `integrating_google` in `localStorage` can be set by any script (XSS, injected content). If an attacker sets it and the user has an active session with a valid `provider_token`, the app will POST the user's Google OAuth token to `/integrations/google` on the next auth event — credential exfiltration.

**Attack:** `localStorage.setItem('integrating_google', 'true')` → trigger page refresh → app POSTs victim's `provider_token` to backend → attacker's token overrides the user's integration.

- [ ] Fix `frontend/src/components/dashboard/SettingsView.jsx:116`:
```javascript
// Replace:
localStorage.setItem('integrating_google', 'true');

// With:
sessionStorage.setItem('integrating_google', 'true');
```

- [ ] Fix `frontend/src/context/AuthContext.jsx` — three locations:
```javascript
// 1. Back/forward navigation cleanup (line ~36-38):
// Replace:
localStorage.removeItem('integrating_google');
// With:
sessionStorage.removeItem('integrating_google');

// 2. Read flag (line ~66):
// Replace:
const isIntegrating = localStorage.getItem('integrating_google') === 'true';
// With:
const isIntegrating = sessionStorage.getItem('integrating_google') === 'true';

// 3. After successful sync (line ~86):
// Replace:
localStorage.removeItem('integrating_google');
// With:
sessionStorage.removeItem('integrating_google');
```

---

## HIGH

---

### [HIGH-BE-5] Enforce SSL on PostgreSQL Connection
**File:** `backend/core/db.py:20-42`

**Problem:** `SUPABASE_DB_URL` is used as-is without enforcing `sslmode=require`. A misconfigured URL without SSL would transmit emails, OAuth tokens, and all user data unencrypted.

- [ ] Fix `backend/core/db.py`:
```python
async def connect(self):
    if self._pool is None:
        db_url = Config.SUPABASE_DB_URL
        # Enforce SSL — append if not already specified
        if "sslmode" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

        self._pool = AsyncConnectionPool(
            conninfo=db_url,
            max_size=30,
            min_size=3,
            open=False,
            check=AsyncConnectionPool.check_connection,
            kwargs={
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
        await self._pool.open()
```

---

### [HIGH-BE-6] OAuth Access Token Exposed in URL Query Parameter
**File:** `backend/routes/integrations.py:26`

**Problem:** `GET ?access_token={creds.token}` sends the Google OAuth token in the URL, where it appears in server access logs, CDN logs, and browser history. RFC 6750 §2.3 marks this as insecure.

- [ ] Fix `backend/routes/integrations.py`:
```python
# Replace:
resp = await client.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={creds.token}")

# With:
resp = await client.get(
    "https://www.googleapis.com/oauth2/v1/tokeninfo",
    headers={"Authorization": f"Bearer {creds.token}"}
)
```

- [ ] Also fix the error log below it to not log `resp.text` (may contain token info):
```python
# Replace:
logger.warning(f"Failed to fetch token info: {resp.text}", extra={"user_id": user.id})

# With:
logger.warning(f"Failed to fetch token info: HTTP {resp.status_code}", extra={"user_id": user.id})
```

---

### [HIGH-BE-7] Provider Parameter Not Whitelisted
**File:** `backend/routes/integrations.py:45-60`

**Problem:** `{provider}` path parameter is passed to the database without validating it's a known provider. Could cause unexpected behavior or leak information about unintended providers.

- [ ] Fix `backend/routes/integrations.py` — add whitelist check to both `GET /{provider}` and `DELETE /{provider}`:
```python
_ALLOWED_PROVIDERS = frozenset({"google"})

@router.get("/{provider}")
async def get_integration_status(provider: str, user: Any = Depends(get_current_user_http)):
    if provider not in _ALLOWED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Invalid provider")
    # ... rest of function unchanged

@router.delete("/{provider}")
async def delete_integration(provider: str, user: Any = Depends(get_current_user_http)):
    if provider not in _ALLOWED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Invalid provider")
    # ... rest of function unchanged
```

---

### [HIGH-BE-8] WebSocket Connection Rate Limiting
**File:** `backend/routes/chat.py:125-139`

**Problem:** Per-message rate limiting exists but there is no limit on connection establishment. Each new connection triggers a full LangGraph state load from PostgreSQL. An attacker can open unlimited concurrent connections.

- [ ] Add to `backend/core/rate_limit.py`:
```python
async def check_ws_connection_limit(user_id: str) -> bool:
    """Limit WebSocket connection attempts to 10 per minute per user."""
    is_allowed, _ = await redis_client.check_rate_limit(
        f"ws_conn:{user_id}", limit=10, window_seconds=60
    )
    return is_allowed
```

- [ ] Fix `backend/routes/chat.py`:
```python
from core.rate_limit import check_ws_connection_limit

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, user: Any = Depends(get_current_user_ws)):
    # Add this block before websocket.accept():
    if not await check_ws_connection_limit(user.id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    # ... rest of function unchanged
```

---

### [HIGH-BE-9] Validate Timezone Parameter
**File:** `backend/routes/chat.py:132-133`

**Problem:** Arbitrary string from WebSocket query param is stored in LangGraph config and used in time operations without validation.

- [ ] Fix `backend/routes/chat.py`:
```python
from zoneinfo import available_timezones as _get_all_tz

_VALID_TIMEZONES = _get_all_tz()  # Module-level constant, computed once on import

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, user: Any = Depends(get_current_user_ws)):
    # ... connection rate limit check and websocket.accept() ...

    user_id = user.id
    # Replace:
    # timezone = websocket.query_params.get("timezone", "UTC")
    # With:
    tz = websocket.query_params.get("timezone", "UTC")
    if tz not in _VALID_TIMEZONES:
        tz = "UTC"

    config = RunnableConfig(configurable={"thread_id": user_id, "timezone": tz})
    # ... rest of function unchanged
```

---

### [HIGH-FE-3] Disable Raw HTML in react-markdown
**File:** `frontend/src/components/dashboard/ChatView.jsx:24-34`

**Problem:** react-markdown renders raw HTML tags by default. If AI output is manipulated (prompt injection) or the backend is compromised, `<img onerror=>` or `<script>` tags in `msg.content` would execute.

- [ ] Fix `frontend/src/components/dashboard/ChatView.jsx`:
```jsx
// Replace:
<Markdown
    components={{
        p: ({node, children, ...props}) => (
            <p className="text-sm whitespace-pre-wrap" {...props}>{children}</p>
        )
    }}
>
    {msg.content}
</Markdown>

// With:
<Markdown
    skipHtml={true}    // Renders HTML tags as plaintext, does not execute them
    components={{
        p: ({node, children, ...props}) => (
            <p className="text-sm whitespace-pre-wrap" {...props}>{children}</p>
        )
    }}
>
    {msg.content}
</Markdown>
```

> All markdown formatting (bold, italic, code blocks, lists) still works. Only raw HTML tags are neutralized.

---

### [HIGH-FE-4] Error Boundary — Remove Stack Trace from User-Facing Output
**File:** `frontend/src/components/dashboard/ErrorBoundary.jsx:25-28`

**Problem:** `{this.state.error?.toString()}` can expose internal file paths, library versions, or sensitive context to users.

- [ ] Fix `frontend/src/components/dashboard/ErrorBoundary.jsx`:
```jsx
// Replace:
<pre className="text-xs text-left bg-gray-200 dark:bg-gray-800 p-4 rounded overflow-auto max-h-40">
    {this.state.error?.toString()}
</pre>

// With:
<pre className="text-xs text-left bg-gray-200 dark:bg-gray-800 p-4 rounded overflow-auto max-h-40">
    An unexpected error occurred. Please refresh the page.
</pre>
```

> Keep `console.error(error, errorInfo)` in the `componentDidCatch` method for dev debugging — just don't show it to users.

---

### [HIGH-FE-5] Content Security Policy
**File:** `frontend/index.html`

**Problem:** No CSP means any injected script runs without restriction — enabling token theft from sessionStorage, unauthorized API calls (reply to emails, create calendar events), and data exfiltration.

- [ ] Add to `<head>` in `frontend/index.html`:
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https://*.supabase.co wss: ws:;
  img-src 'self' data: https:;
  font-src 'self';
  frame-ancestors 'none';
">
```

> In production, replace `wss: ws:` with your specific `VITE_WEBSOCKET_URL` domain. Remove `'unsafe-inline'` from `style-src` once Tailwind CSS is output to a static stylesheet.

---

## MEDIUM

---

### [MEDIUM-BE-10] Enum Validation for `tone` + Length Limits on Rule Fields
**File:** `backend/routes/auto_reply.py:18-29`

**Problem:** `tone` is a free-form string with no allowed-value validation. `when_condition` and `do_action` have only `min_length=1` — no maximum length to prevent oversized prompt injection inputs.

- [ ] Fix `backend/routes/auto_reply.py`:
```python
from enum import Enum

class ToneEnum(str, Enum):
    PROFESSIONAL = "Professional"
    CASUAL = "Casual"
    BRIEF = "Brief"

# Replace:
class AutoReplyRuleCreate(BaseModel):
    name: str = Field(max_length=255)
    when_condition: str = Field(min_length=1)
    do_action: str = Field(min_length=1)
    tone: str = 'Professional'

# With:
class AutoReplyRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    when_condition: str = Field(min_length=1, max_length=500)
    do_action: str = Field(min_length=1, max_length=500)
    tone: ToneEnum = ToneEnum.PROFESSIONAL
```

- [ ] Apply the same changes to `AutoReplyRuleUpdate` in the same file.

---

### [MEDIUM-BE-11] Remove Email Subject (PII) from Auto-Reply Log
**Files:** `backend/services/auto_reply.py:84-95`, `backend/routes/auto_reply.py:226-242`

**Problem:** Email subjects are stored in plaintext in `auto_reply_log` and returned via `GET /auto-reply/log`. Subjects frequently contain sensitive PII (names, medical topics, financial details, salaries).

- [ ] Fix `backend/services/auto_reply.py` — remove `subject` from `log_auto_reply()`:
```python
# Replace:
async def log_auto_reply(user_id, message_id, reply_message_id=None, status='sent', error_message=None, llm_model=None, subject=None):
    await database.execute(
        """INSERT INTO public.auto_reply_log
               (user_id, message_id, reply_message_id, status, error_message, llm_model, subject)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (user_id, message_id) DO NOTHING""",
        (user_id, message_id, reply_message_id, status, error_message, llm_model, subject)
    )

# With:
async def log_auto_reply(user_id, message_id, reply_message_id=None, status='sent', error_message=None, llm_model=None):
    await database.execute(
        """INSERT INTO public.auto_reply_log
               (user_id, message_id, reply_message_id, status, error_message, llm_model)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (user_id, message_id) DO NOTHING""",
        (user_id, message_id, reply_message_id, status, error_message, llm_model)
    )
```

- [ ] Remove all `subject=...` arguments from `log_auto_reply()` call sites in the same file.

- [ ] Fix `backend/routes/auto_reply.py` — remove `subject` from the log endpoint:
```python
# In GET /auto-reply/log, replace:
SELECT id, message_id, replied_at, reply_message_id, status, error_message, llm_model, subject
# With:
SELECT id, message_id, replied_at, reply_message_id, status, error_message, llm_model
```

---

### [MEDIUM-BE-12] File Path Validation in Supabase Client
**File:** `backend/core/supabase_client.py:15-23`

**Problem:** File paths accepted without checking for `..` path traversal. No MIME type whitelist or size limit enforced at the backend layer.

- [ ] Fix `backend/core/supabase_client.py`:
```python
from pathlib import PurePosixPath

_ALLOWED_MIME = {"text/plain", "application/pdf", "image/png", "image/jpeg", "text/csv"}
_MAX_BYTES = 50 * 1024 * 1024  # 50 MB

def _safe_path(path: str) -> str:
    p = PurePosixPath(path)
    if ".." in p.parts or p.is_absolute():
        raise ValueError(f"Invalid file path: {path}")
    return str(p)

async def upload_to_supabase(path: str, file_bytes: bytes, mime_type: str = "text/plain") -> str | None:
    _safe_path(path)
    if mime_type not in _ALLOWED_MIME:
        raise ValueError(f"Disallowed MIME type: {mime_type}")
    if len(file_bytes) > _MAX_BYTES:
        raise ValueError("File exceeds 50MB size limit")
    client = await get_supabase()
    response = await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).upload(
        path, file_bytes, {"content-type": mime_type}
    )
    return response.path

async def download_from_supabase(path: str) -> bytes | None:
    _safe_path(path)
    client = await get_supabase()
    return await client.storage.from_(Config.SUPABASE_USER_FILE_BUCKET).download(path)
```

---

### [MEDIUM-BE-13] Rate Limit WebSocket Ticket Generation
**File:** `backend/routes/auth.py`

**Problem:** No rate limiting on `POST /auth/ticket`. An attacker can generate many tickets in quick succession.

- [ ] Fix `backend/routes/auth.py`:
```python
@router.post("/auth/ticket")
async def get_ws_ticket(user: Any = Depends(get_current_user_http)):
    # Add rate limit: max 5 tickets per minute per user
    is_allowed, _ = await redis_client.check_rate_limit(
        f"ticket_gen:{user.id}", limit=5, window_seconds=60
    )
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    ticket = secrets.token_urlsafe(32)
    await redis_client.set_ws_ticket(ticket, user.id)
    return {"ticket": ticket}
```

---

### [MEDIUM-FE-6] File Upload — Client-Side MIME Type + Size Validation
**File:** `frontend/src/components/dashboard/ChatView.jsx:141-147`

**Problem:** All file types are accepted without client-side filtering. No size limit enforced before upload.

- [ ] Fix `frontend/src/components/dashboard/ChatView.jsx`:
```javascript
const _ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'application/pdf', 'text/plain', 'text/csv']);
const _MAX_SIZE = 10 * 1024 * 1024; // 10 MB

// Replace:
const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setStagedFiles(prev => [...prev, ...files]);
    e.target.value = null;
};

// With:
const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []).filter(file => {
        if (!_ALLOWED_TYPES.has(file.type)) {
            toast.error(`${file.name}: file type not allowed`);
            return false;
        }
        if (file.size > _MAX_SIZE) {
            toast.error(`${file.name}: exceeds 10MB limit`);
            return false;
        }
        return true;
    });
    if (files.length === 0) return;
    setStagedFiles(prev => [...prev, ...files]);
    e.target.value = null;
};
```

---

### [MEDIUM-FE-7] Validate `selectedModel` Against API Response
**File:** `frontend/src/components/dashboard/ChatView.jsx:63-65, 78-80`

**Problem:** Model ID read from `localStorage` is used without verifying it's in the allowed model list returned by the API. An XSS-injected value could cause unexpected API errors.

- [ ] Fix `frontend/src/components/dashboard/ChatView.jsx` — after fetching models:
```javascript
// Replace:
if (!localStorage.getItem('selectedModel')) {
    setSelectedModel(data.default);
}

// With:
const validIds = new Set(data.models.map(m => m.id));
const stored = localStorage.getItem('selectedModel');
setSelectedModel(validIds.has(stored) ? stored : data.default);
```

---

## Verification Checklist

### Backend
- [ ] Timing-safe comparisons: Send `POST /webhooks/gmail` with wrong tokens of varying lengths — response time must not vary with token length
- [ ] OIDC validation: Send a valid Google OIDC token from a different service account — should get 401
- [ ] Security headers: `curl -I https://your-api.com/health` — verify `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security` present
- [ ] Redis SSL: Verify Redis Labs dashboard shows encrypted connections
- [ ] PostgreSQL SSL: Check connection string includes `sslmode=require`
- [ ] Provider whitelist: `GET /integrations/microsoft` → 400 "Invalid provider"
- [ ] Timezone validation: Connect WebSocket with `?timezone=../etc/passwd` — server falls back to UTC silently
- [ ] WS connection rate limit: Open 11 WebSocket connections from the same user in 1 minute — 11th is immediately closed
- [ ] Rule tone validation: `POST /auto-reply/rules` with `"tone": "Aggressive"` → 422 validation error
- [ ] Auto-reply log PII: Trigger an auto-reply; `GET /auto-reply/log` must NOT include a `subject` field

### Frontend
- [ ] sessionStorage: After login, DevTools → Application → LocalStorage — Supabase tokens must NOT appear there; check SessionStorage
- [ ] CSP: In DevTools Console, run `eval("1+1")` — should throw `EvalError: Refused to evaluate`
- [ ] react-markdown: Craft a response with `<img src=x onerror="alert(1)">` — must render as literal text, not execute
- [ ] File upload type: Upload a `.exe` file — toast error "file type not allowed", not added to staged list
- [ ] Error boundary: Temporarily throw in a component — only "An unexpected error occurred" shown, no stack trace
