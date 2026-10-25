# Walk with God — Backend API

FastAPI service for the Walk with God journey application.

## Local setup (Windows PowerShell)

```powershell
cd C:\dev\Walk_with_God\backend
uv sync                      # creates .venv and installs dependencies
Copy-Item .env.example .env  # local settings (never commit .env)
uv run pytest                # run the test suite
uv run uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs (development only) or
http://127.0.0.1:8000/api/v1/health.

## Layout

```
app/
  main.py            application factory (create_app)
  core/              configuration, logging, error handling
  api/v1/            versioned HTTP routers
tests/               pytest suite (HTTPX + ASGI transport)
```

## Rules

- Secrets live in `.env` (ignored by Git) or real environment variables.
- Business rules, authorization and sequencing belong on the server.
- Every new endpoint needs a test before it is considered done.
