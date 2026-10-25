# Walk with God

An AI-assisted, Jesus-centered spiritual journey through Scripture, prayer,
reflection, and fellowship. Built as a modular monolith: a React + TypeScript
frontend talking to a Python FastAPI backend, with PostgreSQL, Supabase Auth,
Google Gemini (behind a replaceable adapter), and Web Push reminders.

The curriculum is a fixed sequence of **387 Walks across 15 Parts**, and every
Walk has six sections: Main Passages, Bible History, Walking with God,
God's Connections, Treasure to Keep, and Short Walk Prayer.

> Status: **Stage 1 — foundation.** Only the backend skeleton, health check,
> error handling, and test harness exist so far.

## Repository layout

```
backend/            FastAPI service (Python 3.11+, uv)
frontend/           React + Vite + TypeScript + Tailwind (Stage 2+)
docs/               design notes and decisions
```

## Quick start

```powershell
cd backend
uv sync
Copy-Item .env.example .env
uv run pytest
uv run uvicorn app.main:app --reload
```

Health check: <http://127.0.0.1:8000/api/v1/health>

## Principles

- **Server-authoritative.** Walk sequencing, prerequisites, completion, and
  authorization are decided by the backend, never by the AI or the browser.
- **Scripture is not AI.** Bible text and AI-generated explanation are stored
  and displayed separately, and labeled.
- **Private by default.** Notes, reflections, prayer records, and progress are
  scoped to the owning user and checked on every request.
- **Secrets stay server-side.** Only placeholders live in `.env.example`.
- **Small verified steps.** Every stage ends with passing tests.

## Roadmap

| Stage | Scope |
|---|---|
| 1 | Repo foundation, FastAPI skeleton, error envelope, tests, health check |
| 2 | React + Vite + TypeScript + Tailwind shell |
| 3 | PostgreSQL (Supabase), SQLAlchemy models, Alembic migrations |
| 4 | Supabase Auth, JWT verification (JWKS), ownership enforcement |
| 5 | Curriculum, sequencing, six-section Walk UI, progress/notes/reflections/time |
| 6 | WEB Classic validation + import, passage display |
| 7 | AI provider interface, Gemini adapter, safety and usage limits |
| 8 | Prayer scheduling, service worker, Web Push, persistent reminder worker |
| 9 | E2E tests, security review, deployment, documentation |
