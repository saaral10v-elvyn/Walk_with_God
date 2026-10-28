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
  auth/              JWKS cache, token verification, profile service
  core/              configuration, logging, error handling
  api/v1/            versioned HTTP routers
  db/                async engine, sessions, ORM models
alembic/             migration environment and versions
scripts/db_check.py  sanitized connection smoke test
tests/               pytest suite (HTTPX + ASGI transport)
```

## Database

Supabase Postgres (Session pooler) with SQLAlchemy 2 async + asyncpg.

```powershell
uv run python scripts/db_check.py      # prints "connected" or a sanitized category
uv run alembic current                 # applied revision
uv run alembic upgrade head            # apply migrations
uv run alembic revision --autogenerate -m "describe change"
```

The database URL lives only in `.env`. TLS defaults to `DB_SSL_MODE=require`
(encrypted, no certificate verification), which is Supabase's documented
default because the pooler uses a private CA. For full verification, download
the root certificate from Supabase → Database settings, set `DB_SSL_CA_FILE`,
and use `DB_SSL_MODE=verify-full`.

Integration tests are skipped unless explicitly enabled:

```powershell
$env:RUN_DB_TESTS="1"; uv run pytest tests/test_db_integration.py
```

## Authentication

Supabase Auth issues the access tokens. The backend verifies each one against
the project's JWKS endpoint and never trusts a user id supplied by the browser.

Configure these in `.env` (never commit them):

```dotenv
SUPABASE_URL="https://YOUR_PROJECT_REF.supabase.co"
# Optional; derived from SUPABASE_URL when omitted.
SUPABASE_JWKS_URL="https://YOUR_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json"
SUPABASE_JWT_ISSUER="https://YOUR_PROJECT_REF.supabase.co/auth/v1"
SUPABASE_JWT_AUDIENCE="authenticated"
```

The project must use an **asymmetric** JWT signing key (Supabase Dashboard →
Authentication → Signing Keys, normally ECC P-256 / ES256). The legacy shared
HS256 secret cannot be verified through JWKS, and this backend deliberately
rejects HMAC and `none` algorithms.

`GET /api/v1/auth/me` requires `Authorization: Bearer <access token>` and
returns the caller's profile, creating the `users` row on first sign-in. Every
future user-owned endpoint must depend on `get_current_identity` and scope its
queries by `identity.user_id`.

Verification failures return `401 unauthorized`; a server without auth settings
returns `503 auth_not_configured`; an unreachable JWKS endpoint returns
`503 auth_unavailable`. Tokens and key material are never logged.

## Rules

- Secrets live in `.env` (ignored by Git) or real environment variables.
- Business rules, authorization and sequencing belong on the server.
- Every new endpoint needs a test before it is considered done.
- Never let AI code decide unlocking, completion, or permissions.
