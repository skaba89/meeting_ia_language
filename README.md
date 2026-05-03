# MeetingAI Copilot

**Intelligent meeting assistant for international teams** — Transcribe, summarize, and translate your meetings with AI.

Built with FastAPI, Next.js, Whisper, and LLM technology.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    MeetingAI Copilot                      │
├──────────────┬──────────────────┬────────────────────────┤
│   Frontend   │     Backend      │      AI Services       │
│  Next.js 16  │   FastAPI         │   Whisper (STT)       │
│  React 19    │   SQLAlchemy      │   LLM (Summary)       │
│  Tailwind    │   JWT Auth        │   Translation         │
│  shadcn/ui   │   PostgreSQL      │   OpenRouter/Groq     │
└──────┬───────┴────────┬─────────┴────────────────────────┘
       │                │
       │   REST API     │
       │◄──────────────►│
       │                │
┌──────┴───────┐  ┌────┴─────────┐
│   Browser    │  │  PostgreSQL  │
│   :3000      │  │  :5432       │
└──────────────┘  └──────────────┘
```

### Tech Stack

| Layer       | Technology                          | Purpose                          |
|-------------|-------------------------------------|----------------------------------|
| Frontend    | Next.js 16, React 19, TypeScript   | UI, routing, state management   |
| UI Library  | shadcn/ui, Tailwind CSS 4          | Professional SaaS-style components |
| Backend     | FastAPI, Python 3.12               | REST API, business logic        |
| Database    | PostgreSQL (prod) / SQLite (dev)   | Users, meetings, metadata       |
| Auth        | JWT (python-jose + bcrypt)          | Secure token-based auth         |
| Transcription | OpenAI Whisper API                | Speech-to-text                  |
| Summarization | OpenRouter / Groq LLM API        | Structured meeting summaries    |
| Translation   | LLM-based translation            | Multi-language support          |
| Containerization | Docker, docker-compose       | Reproducible deployments        |

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed
- **API Keys** (optional for demo mode):
  - [OpenRouter](https://openrouter.ai) key for AI summaries
  - [OpenAI](https://platform.openai.com) key for Whisper transcription

### 1. Clone and Configure

```bash
git clone <repo-url> && cd meetingai-copilot

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Launch with Docker

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build
```

### 3. Access the Application

| Service     | URL                          |
|-------------|------------------------------|
| Frontend    | http://localhost:3000        |
| Backend API | http://localhost:8000        |
| API Docs    | http://localhost:8000/docs   |
| Health      | http://localhost:8000/health |

### 4. Create an Account

1. Open http://localhost:3000
2. Click "Sign up" to create an account
3. Upload your first meeting audio file
4. Click "Transcribe" then "Summarize"

---

## API Endpoints

### Authentication

| Method | Endpoint          | Description        |
|--------|-------------------|--------------------|
| POST   | `/auth/register`  | Create new account |
| POST   | `/auth/login`     | Get JWT token      |

### Meetings

| Method | Endpoint               | Description                    |
|--------|------------------------|--------------------------------|
| POST   | `/meetings/upload`     | Upload audio file              |
| GET    | `/meetings/`           | List all meetings              |
| GET    | `/meetings/{id}`       | Get meeting details            |
| POST   | `/meetings/transcribe` | Transcribe audio with Whisper  |
| POST   | `/meetings/summary`    | Generate AI summary + optional translation |
| PATCH  | `/meetings/{id}`       | Update meeting metadata        |
| DELETE | `/meetings/{id}`       | Delete meeting                 |

### Health

| Method | Endpoint   | Description        |
|--------|------------|--------------------|
| GET    | `/`        | Basic health check |
| GET    | `/health`  | Detailed status    |

### API Request Examples

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"John","password":"secure123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Upload audio
curl -X POST http://localhost:8000/meetings/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@meeting.mp3" \
  -F "title=Team Standup"

# Transcribe
curl -X POST http://localhost:8000/meetings/transcribe \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"meeting_id":"<MEETING_ID>"}'

# Summarize with translation
curl -X POST http://localhost:8000/meetings/summary \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"meeting_id":"<MEETING_ID>","target_lang":"fr"}'
```

---

## Project Structure

```
meetingai-copilot/
├── backend/                        # FastAPI backend
│   ├── app/
│   │   ├── main.py                # Application entry point
│   │   ├── core/
│   │   │   ├── config.py          # Settings & env variables
│   │   │   ├── database.py        # SQLAlchemy engine & sessions
│   │   │   └── security.py        # JWT & password hashing
│   │   ├── models/
│   │   │   └── schemas.py         # ORM models & Pydantic schemas
│   │   ├── api/
│   │   │   ├── auth.py            # /auth/register, /auth/login
│   │   │   └── meetings.py        # /meetings/* endpoints
│   │   └── services/
│   │       ├── transcription.py   # Whisper integration
│   │       └── summary.py         # LLM summary & translation
│   ├── uploads/                   # Audio file storage
│   ├── requirements.txt           # Python dependencies
│   └── .env                       # Backend environment
│
├── frontend/                       # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── page.tsx           # Main page (auth/dashboard)
│   │   │   └── globals.css        # Global styles
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   └── auth-page.tsx  # Login/Register form
│   │   │   ├── dashboard/
│   │   │   │   ├── dashboard.tsx  # Main dashboard
│   │   │   │   └── meeting-detail.tsx  # Meeting detail view
│   │   │   ├── upload/
│   │   │   │   └── audio-upload.tsx    # Drag & drop upload
│   │   │   └── ui/               # shadcn/ui components
│   │   └── lib/
│   │       ├── api-client.ts      # API client with auth
│   │       ├── auth-store.ts      # Zustand auth state
│   │       └── utils.ts           # Utility functions
│   ├── package.json
│   └── ...
│
├── docker-compose.yml             # Full stack orchestration
├── Dockerfile.backend             # Backend container
├── Dockerfile.frontend            # Frontend container
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## Environment Variables

| Variable                    | Default                                  | Description                              |
|-----------------------------|------------------------------------------|------------------------------------------|
| `SECRET_KEY`               | `meetingai-change-this-...`              | JWT signing key (CHANGE IN PRODUCTION!) |
| `LLM_API_KEY`              | _(empty)_                                | OpenRouter or Groq API key              |
| `LLM_API_BASE`             | `https://openrouter.ai/api/v1`          | LLM API base URL                        |
| `LLM_MODEL`                | `openai/gpt-3.5-turbo`                  | LLM model identifier                    |
| `WHISPER_MODE`             | `api`                                    | `api` = OpenAI, `local` = openai-whisper |
| `OPENAI_API_KEY`           | _(empty)_                                | OpenAI API key for Whisper              |
| `TRANSLATION_ENABLED`      | `true`                                   | Enable/disable translation feature      |
| `DEFAULT_TARGET_LANG`      | `en`                                     | Default translation language            |
| `MAX_UPLOAD_SIZE_MB`       | `100`                                    | Maximum audio file size                 |

---

## Demo Mode

MeetingAI Copilot works **without any API keys** in demo mode:

- **Transcription**: Returns a placeholder message explaining how to configure Whisper
- **Summary**: Returns demo decisions, action items, and overview
- **Translation**: Returns a placeholder translation message

To enable full AI features:
1. Get an API key from [OpenRouter](https://openrouter.ai) (free tier available)
2. Set `LLM_API_KEY` in your `.env` file
3. For Whisper, set `OPENAI_API_KEY` or switch to `WHISPER_MODE=local`

---

## Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
bun install
bun run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
bun run lint
```

---

## Production Considerations

- **Change SECRET_KEY**: Use a strong, randomly generated key
- **Use PostgreSQL**: Set `API_DATABASE_URL` to a managed PostgreSQL instance
- **Enable HTTPS**: Use a reverse proxy (Nginx, Caddy) with TLS
- **Set CORS origins**: Restrict `allow_origins` in `main.py`
- **Add rate limiting**: Protect auth endpoints from brute force
- **Use object storage**: Replace local uploads with S3/GCS for scalability
- **Add monitoring**: Integrate Sentry, DataDog, or similar APM
- **Enable CI/CD**: GitHub Actions, GitLab CI for automated testing and deployment

---

## License

MIT
