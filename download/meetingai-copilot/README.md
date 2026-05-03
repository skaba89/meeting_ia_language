# MeetingAI Copilot

**Intelligent Meeting Assistant** — Transcribe, summarize, and translate your meeting recordings with AI.

## Features

- **Audio Transcription** — Upload MP3/WAV/M4A/WebM/OGG/FLAC recordings and get accurate transcriptions powered by Groq Whisper (whisper-large-v3) with automatic chunking for large files
- **Smart Summaries** — Generate structured summaries with executive overview, key decisions, action items, and participants using LLM (Llama 3.3 70B)
- **Multi-language Translation** — Automatically translate transcriptions to 16 supported languages
- **Refresh Token Authentication** — Secure JWT system with access tokens (60 min) and refresh tokens (7 days) with token rotation and blacklisting
- **Account Security** — Account lockout after 5 failed login attempts, password strength validation, and input sanitization
- **Structured Error Handling** — Custom exception hierarchy with consistent JSON error responses and request tracking
- **Input Validation** — SQL injection detection, XSS sanitization, file upload constraints, and language code validation
- **Structured Logging** — JSON-formatted logs with request IDs, user IDs, and timing information
- **Application Metrics** — Request counters, gauges, timers with p95 statistics (authenticated endpoint)
- **Comprehensive Health Checks** — Database, Redis, AI service configuration, and system resource monitoring
- **Rate Limiting** — Redis-backed rate limiting with in-memory fallback
- **Async Processing** — Celery-based background workers for transcription, summarization, and translation
- **Dual LLM Provider** — Automatic fallback between Groq and OpenRouter with retry logic
- **Meeting History** — Browse, search, and manage all your past meetings

## Architecture

```
┌──────────────────┐     ┌──────────────────────────────────────────┐     ┌──────────────┐
│   Next.js 14     │     │         FastAPI 0.115 Backend            │     │  PostgreSQL  │
│   Frontend       │────▶│  ┌──────────────────────────────────┐    │────▶│  or SQLite   │
│   (Port 3000)    │◀────│  │  Middleware Stack:                │    │◀────│              │
└──────────────────┘     │  │  • Request Logging (X-Request-ID) │    │     └──────────────┘
                         │  │  • Error Handler                  │    │
                         │  │  • CORS (specific methods)        │    │     ┌──────────────┐
                         │  │  • Security Headers (7 headers)   │    │────▶│    Redis     │
                         │  │  • Rate Limiting (SlowAPI)        │    │     │  (cache +    │
                         │  │  • Request ID Injection           │    │     │   broker)    │
                         │  └──────────────────────────────────┘    │     └──────────────┘
                         │                                          │
                         │  ┌──────────┐  ┌────────────────────┐   │     ┌──────────────┐
                         │  │ API v1   │  │ Core               │   │     │    Celery     │
                         │  │ /auth/*  │  │ • Logging          │   │────▶│   Worker     │
                         │  │ /meetings│  │ • Exceptions       │   │     │  (AI tasks)  │
                         │  │ /metrics │  │ • Validators       │   │     └──────────────┘
                         │  └──────────┘  │ • Metrics          │   │
                         │                └────────────────────┘   │
                         └──────────────────────────────────────────┘
                                    │                    │
                          ┌─────────┴──────┐   ┌────────┴────────┐
                          │     Groq       │   │   OpenRouter     │
                          │  Whisper + LLM │   │   LLM (fallback) │
                          └────────────────┘   └─────────────────┘
```

## Quick Start (Local Development — No Docker Needed)

The easiest way to get started is using **SQLite** (no PostgreSQL installation required).

### Prerequisites

- Python 3.12+
- Node.js 20+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# The .env file is already configured with SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./meetingai.db
# Just add your Groq API key to backend/.env

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### 3. Access the application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 4. Create an account and start using

1. Open http://localhost:3000
2. Click "Get Started Free" to register
3. Upload a meeting recording (MP3, WAV, M4A, OGG, FLAC, or WebM)
4. Click "Transcribe" to generate a transcription
5. Click "Generate Summary" to get a structured summary
6. Use "Translate" to translate the transcription to another language

---

## Quick Start (Docker — Production with PostgreSQL)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Groq API key

### 1. Configure API keys

```bash
cd meetingai-copilot

# Create .env from the example and add your API keys
cp .env.example .env
nano .env
```

Set at minimum:
```
SECRET_KEY=<generate-a-strong-random-key-at-least-32-chars>
GROQ_API_KEY=<your-groq-api-key>
```

### 2. Switch backend to PostgreSQL

Edit `backend/.env` and change:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/meetingai
```

### 3. Launch with Docker Compose

```bash
docker compose up --build
```

This starts all services:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend API** on port 8000
- **Celery Worker** (background AI processing)
- **Frontend** on port 3000

---

## Tech Stack

| Layer       | Technology                                              |
|-------------|---------------------------------------------------------|
| Frontend    | Next.js 14, React 18, TypeScript, Tailwind CSS          |
| Backend     | FastAPI 0.115, SQLAlchemy 2.0 (async), Pydantic 2       |
| Database    | PostgreSQL 16 (Docker) / SQLite (local dev)             |
| Cache/Broker| Redis 7 (rate limiting, Celery broker, token blacklist) |
| Task Queue  | Celery 5.4 with Redis backend                           |
| AI - STT    | Groq Whisper API (whisper-large-v3)                     |
| AI - LLM    | Groq (llama-3.3-70b-versatile) / OpenRouter (fallback)  |
| Auth        | JWT (python-jose) + bcrypt (passlib) with refresh tokens|
| Monitoring  | Structured JSON logging, application metrics, health checks |
| Security    | Security headers, rate limiting, input validation, account lockout |
| Container   | Docker Compose with multi-stage builds                  |

## API Endpoints

All API endpoints are versioned under `/api/v1`.

### Authentication

| Method | Endpoint              | Auth Required | Description                                    |
|--------|-----------------------|---------------|------------------------------------------------|
| POST   | `/api/v1/auth/register` | No          | Register new user (email, password, full_name) |
| POST   | `/api/v1/auth/login`    | No          | Login and get access + refresh tokens           |
| POST   | `/api/v1/auth/refresh`  | No*         | Refresh access token using refresh token        |
| POST   | `/api/v1/auth/logout`   | Yes         | Blacklist refresh token (revoke)                |
| GET    | `/api/v1/auth/me`       | Yes         | Get current user profile                        |

\* The `/auth/refresh` endpoint requires a valid refresh token in the body, not an access token.

### Meetings

| Method | Endpoint                             | Auth Required | Description                        |
|--------|--------------------------------------|---------------|------------------------------------|
| POST   | `/api/v1/meetings/upload`           | Yes           | Upload audio file + create meeting |
| POST   | `/api/v1/meetings/{id}/transcribe`  | Yes           | Start transcription (async)        |
| POST   | `/api/v1/meetings/{id}/summary`     | Yes           | Generate summary (async)           |
| POST   | `/api/v1/meetings/{id}/translate`   | Yes           | Translate transcription (async)    |
| GET    | `/api/v1/meetings/`                 | Yes           | List user meetings (paginated)     |
| GET    | `/api/v1/meetings/{id}`             | Yes           | Get meeting details                |
| DELETE | `/api/v1/meetings/{id}`             | Yes           | Delete meeting + audio file        |

### Monitoring & Health

| Method | Endpoint              | Auth Required | Description                                    |
|--------|-----------------------|---------------|------------------------------------------------|
| GET    | `/health`             | No            | Health check (DB, Redis, AI keys, system info) |
| GET    | `/api/v1/metrics`     | Yes           | Application metrics (counters, timers, gauges) |

### Supported Languages for Translation

| Code | Language  | Code | Language |
|------|-----------|------|----------|
| en   | English   | ja   | Japanese |
| fr   | French    | ko   | Korean   |
| es   | Spanish   | ar   | Arabic   |
| de   | German    | hi   | Hindi    |
| it   | Italian   | tr   | Turkish  |
| pt   | Portuguese| pl   | Polish   |
| nl   | Dutch     | sv   | Swedish  |
| ru   | Russian   | zh   | Chinese  |

## Project Structure

```
meetingai-copilot/
├── docker-compose.yml
├── .env.example
├── .env
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── .env
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app + lifespan + middleware stack
│       ├── config.py            # Settings (pydantic-settings)
│       ├── database.py          # Async SQLAlchemy (PostgreSQL/SQLite)
│       ├── celery_worker.py     # Celery configuration
│       ├── tasks.py             # Celery tasks (transcription, summary, translation)
│       ├── core/
│       │   ├── __init__.py      # Core package exports
│       │   ├── logging.py       # Structured JSON logging
│       │   ├── exceptions.py    # Custom exception hierarchy
│       │   ├── validators.py    # Input validation utilities
│       │   └── metrics.py       # Application metrics collector
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py          # User model (UUID PK, lockout fields)
│       │   └── meeting.py       # Meeting model + Status enum
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py          # Auth request/response schemas + validators
│       │   └── meeting.py       # Meeting schemas + SummarySchema + TranslationRequest
│       ├── api/
│       │   ├── __init__.py
│       │   ├── auth.py          # /auth/* routes (register, login, refresh, logout, me)
│       │   └── meetings.py      # /meetings/* routes (upload, transcribe, summary, translate)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py  # JWT + password hashing
│       │   ├── token_service.py # Token management (create, decode, blacklist, refresh)
│       │   ├── transcription_service.py  # Groq Whisper with chunking
│       │   ├── summary_service.py        # LLM summarization with JSON extraction
│       │   ├── translation_service.py    # LLM translation
│       │   └── llm_client.py             # Unified LLM client with retry + fallback
│       ├── middleware/
│       │   ├── __init__.py      # Middleware package exports
│       │   ├── auth_middleware.py     # JWT verification + refresh token validation
│       │   ├── error_handler.py       # Global error handler middleware
│       │   ├── request_logging.py     # Request logging with timing
│       │   └── validation.py          # File upload, SQL injection, XSS validation
│       ├── alembic/             # Database migrations
│       └── tests/               # Test suite (112 tests)
│           ├── conftest.py
│           ├── api/
│           ├── services/
│           └── core/
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx              # Landing page
        │   ├── globals.css
        │   ├── login/page.tsx
        │   ├── register/page.tsx
        │   ├── dashboard/page.tsx
        │   └── meeting/[id]/page.tsx  # Meeting detail
        ├── components/
        │   ├── Navbar.tsx
        │   ├── AudioUpload.tsx
        │   ├── TranscriptionView.tsx
        │   ├── SummaryView.tsx
        │   ├── MeetingCard.tsx
        │   ├── Toast.tsx             # Toast notification system
        │   └── LoadingSpinner.tsx    # Loading spinner components
        ├── hooks/
        │   └── usePolling.ts         # Polling hook for async processing
        ├── lib/
        │   ├── api.ts               # API client with retry logic
        │   └── auth.ts              # Token storage utilities
        └── contexts/
            └── AuthContext.tsx       # Auth state provider with auto-refresh
```

## Environment Variables

### Backend

| Variable                        | Default                                        | Description                                      |
|---------------------------------|------------------------------------------------|--------------------------------------------------|
| `DATABASE_URL`                  | `sqlite+aiosqlite:///./meetingai.db`           | DB connection (SQLite or PostgreSQL)             |
| `SECRET_KEY`                    | **Required** (≥32 chars)                       | JWT signing key (must not be a known default)    |
| `ALGORITHM`                     | `HS256`                                        | JWT algorithm                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES`   | `60`                                           | Access token expiration time (minutes)           |
| `REFRESH_TOKEN_EXPIRE_DAYS`     | `7`                                            | Refresh token expiration time (days)             |
| `GROQ_API_KEY`                  | —                                              | Groq API key (required for transcription + LLM)  |
| `OPENROUTER_API_KEY`            | —                                              | OpenRouter API key (optional, used as fallback)   |
| `WHISPER_MODEL_SIZE`            | `base`                                         | Whisper model size                               |
| `LLM_PROVIDER`                  | `groq`                                         | Primary LLM provider: `groq` or `openrouter`     |
| `GROQ_MODEL`                    | `llama-3.3-70b-versatile`                      | Groq model name for chat completions             |
| `OPENROUTER_MODEL`              | `meta-llama/llama-3.3-70b-instruct`            | OpenRouter model name for chat completions        |
| `UPLOAD_DIR`                    | `./uploads`                                    | Audio upload directory                           |
| `MAX_UPLOAD_SIZE_MB`            | `100`                                          | Max upload size in MB                            |
| `CORS_ORIGINS`                  | `http://localhost:3000`                        | Comma-separated allowed CORS origins             |
| `REDIS_URL`                     | `redis://redis:6379/0`                         | Redis URL (rate limiting, Celery, token blacklist)|
| `RATE_LIMIT_PER_MINUTE`         | `60`                                           | Max requests per minute per client IP            |
| `LOG_LEVEL`                     | `INFO`                                         | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |

### Frontend

| Variable              | Default                    | Description              |
|-----------------------|----------------------------|--------------------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`    | Backend API base URL     |

## Security Features

### Authentication & Authorization
- **JWT Access Tokens**: Short-lived (60 min default) with type validation
- **JWT Refresh Tokens**: Long-lived (7 days default) with rotation on refresh
- **Token Blacklisting**: Redis-backed with in-memory fallback
- **Account Lockout**: 5 failed login attempts → 30 minute lockout
- **Password Strength**: Minimum 8 chars, requires uppercase, lowercase, and digit

### Input Validation
- **SQL Injection Detection**: Pattern matching for common injection vectors
- **XSS Sanitization**: Script tags, event handlers, javascript: protocol, dangerous HTML
- **File Upload Validation**: Extension allowlist, MIME type checking, max size enforcement
- **Language Code Validation**: Against 16 supported languages

### HTTP Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy` (restrictive default-src)
- `Strict-Transport-Security` (1 year with preload)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (camera, microphone, geolocation, payment disabled)

### Rate Limiting
- Redis-backed rate limiting via SlowAPI
- Configurable per-minute limit (default: 60)
- In-memory fallback when Redis is unavailable

## Testing

The project includes a comprehensive test suite with 112 tests.

### Run all tests

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test modules
pytest tests/api/test_auth.py -v
pytest tests/api/test_meetings.py -v
pytest tests/core/test_validators.py -v
pytest tests/services/test_token_service.py -v
```

### Test categories

| Category | File | Tests | Description |
|----------|------|-------|-------------|
| Auth API | `tests/api/test_auth.py` | 18 | Registration, login, refresh, logout, edge cases |
| Meetings API | `tests/api/test_meetings.py` | 17 | Upload, transcribe, summary, list, delete |
| Validators | `tests/core/test_validators.py` | 33 | Language codes, passwords, emails, XSS, file validation |
| Token Service | `tests/services/test_token_service.py` | 22 | Token creation, decoding, blacklisting, refresh rotation |

## LLM Provider Configuration

### Groq (default, recommended)

Set `LLM_PROVIDER=groq` in your environment. Uses:
- **Transcription**: `whisper-large-v3` via Groq's Whisper API
- **Summarization**: `llama-3.3-70b-versatile` via Groq's Chat API
- **Translation**: `llama-3.3-70b-versatile` via Groq's Chat API

### OpenRouter (alternative)

Set `LLM_PROVIDER=openrouter` in your environment. Uses:
- **Transcription**: Still uses Groq Whisper (only LLM switches)
- **Summarization**: `meta-llama/llama-3.3-70b-instruct` via OpenRouter
- **Translation**: `meta-llama/llama-3.3-70b-instruct` via OpenRouter

### Automatic Fallback

When the primary LLM provider fails, the system automatically falls back to the alternative provider with exponential backoff retry logic (3 attempts, 1s/2s/4s delays).

## Error Handling

All errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description of what went wrong",
    "details": {},
    "request_id": "abc12345"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Invalid or expired credentials |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate resource (e.g., email) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `FILE_TOO_LARGE` | 413 | Upload exceeds size limit |
| `UNSUPPORTED_FILE_TYPE` | 415 | File type not allowed |
| `EXTERNAL_SERVICE_ERROR` | 502 | Groq/OpenRouter API failure |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## License

MIT
