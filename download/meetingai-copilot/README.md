# MeetingAI Copilot

**Intelligent Meeting Assistant** — Transcribe, summarize, and translate your meeting recordings with AI.

## Features

- **Audio Transcription** — Upload MP3/WAV/M4A/WebM recordings and get accurate transcriptions powered by Groq Whisper (whisper-large-v3)
- **Smart Summaries** — Generate structured summaries with executive overview, key decisions, action items, and participants using LLM (Llama 3.3 70B)
- **Multi-language Translation** — Automatically translate transcriptions to 10+ languages
- **Meeting History** — Browse, search, and manage all your past meetings
- **JWT Authentication** — Secure user registration and login with JWT tokens

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Next.js 14    │────▶│   FastAPI 0.115  │────▶│ PostgreSQL  │
│   Frontend      │◀────│   Backend        │◀────│ or SQLite   │
│   (Port 3000)   │     │   (Port 8000)    │     │             │
└─────────────────┘     └────────┬────────┘     └─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐           ┌──────▼──────┐
              │   Groq    │           │ OpenRouter  │
              │  Whisper  │           │    LLM      │
              │  + LLM    │           │  (optional) │
              └───────────┘           └─────────────┘
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

### 4. Create an account and start using

1. Open http://localhost:3000
2. Click "Get Started Free" to register
3. Upload a meeting recording (MP3, WAV, M4A, or WebM)
4. Click "Transcribe" to generate a transcription
5. Click "Generate Summary" to get a structured summary

---

## Quick Start (Docker — Production with PostgreSQL)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Groq API key

### 1. Configure API keys

```bash
cd meetingai-copilot

# Edit .env and add your GROQ_API_KEY and OPENROUTER_API_KEY
nano .env
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

---

## Tech Stack

| Layer       | Technology                                  |
|-------------|---------------------------------------------|
| Frontend    | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend     | FastAPI 0.115, SQLAlchemy 2.0 (async), Pydantic 2 |
| Database    | PostgreSQL 16 (Docker) / SQLite (local dev) |
| AI - STT    | Groq Whisper API (whisper-large-v3)         |
| AI - LLM    | Groq (llama-3.3-70b-versatile) / OpenRouter |
| Auth        | JWT (python-jose) + bcrypt (passlib)        |
| Container   | Docker Compose                              |

## API Endpoints

### Authentication

| Method | Endpoint           | Description          |
|--------|--------------------|----------------------|
| POST   | `/auth/register`   | Register new user    |
| POST   | `/auth/login`      | Login and get token  |
| GET    | `/auth/me`         | Get current user     |

### Meetings

| Method | Endpoint                        | Description               |
|--------|---------------------------------|---------------------------|
| POST   | `/meetings/upload`              | Upload audio file         |
| POST   | `/meetings/{id}/transcribe`     | Transcribe meeting audio  |
| POST   | `/meetings/{id}/summary`        | Generate meeting summary  |
| GET    | `/meetings/`                    | List user meetings        |
| GET    | `/meetings/{id}`                | Get meeting details       |
| DELETE | `/meetings/{id}`                | Delete meeting            |

### Health

| Method | Endpoint   | Description       |
|--------|------------|-------------------|
| GET    | `/health`  | Health check      |

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
│   ├── .env
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app + lifespan
│       ├── config.py            # Settings (pydantic-settings)
│       ├── database.py          # Async SQLAlchemy (PostgreSQL/SQLite)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py          # User model (UUID PK)
│       │   └── meeting.py       # Meeting model + Status enum
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py          # Auth request/response schemas
│       │   └── meeting.py       # Meeting schemas + SummarySchema
│       ├── api/
│       │   ├── __init__.py
│       │   ├── auth.py          # /auth/* routes
│       │   └── meetings.py      # /meetings/* routes
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py  # JWT + password hashing
│       │   ├── transcription_service.py  # Groq Whisper
│       │   ├── summary_service.py        # LLM summarization
│       │   └── translation_service.py    # LLM translation
│       └── middleware/
│           ├── __init__.py
│           └── auth_middleware.py  # JWT verification dependency
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
        │   └── MeetingCard.tsx
        ├── lib/
        │   ├── api.ts               # API client
        │   └── auth.ts              # Token storage utilities
        └── contexts/
            └── AuthContext.tsx       # Auth state provider
```

## Environment Variables

| Variable                      | Default                                  | Description                        |
|-------------------------------|------------------------------------------|------------------------------------|
| `DATABASE_URL`                | `sqlite+aiosqlite:///./meetingai.db`     | DB connection (SQLite or PostgreSQL) |
| `SECRET_KEY`                  | `meetingai-super-secret-key-...`         | JWT signing key                    |
| `ALGORITHM`                   | `HS256`                                  | JWT algorithm                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                                     | Token expiration time              |
| `GROQ_API_KEY`                | —                                        | Groq API key (required)            |
| `OPENROUTER_API_KEY`          | —                                        | OpenRouter API key (optional)      |
| `WHISPER_MODEL_SIZE`          | `base`                                   | Whisper model size                 |
| `LLM_PROVIDER`                | `groq`                                   | LLM provider: `groq` or `openrouter` |
| `UPLOAD_DIR`                  | `./uploads`                              | Audio upload directory             |
| `MAX_UPLOAD_SIZE_MB`          | `100`                                    | Max upload size in MB              |
| `NEXT_PUBLIC_API_URL`         | `http://localhost:8000`                  | Backend URL (frontend only)        |

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

## License

MIT
