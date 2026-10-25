# Architecture decisions log

Short records of decisions that shape the build. Update this file whenever a
decision changes, so future work does not have to rediscover the reasoning.

## AD-001 — Modular monolith
**Status:** accepted (Architecture V1.0)
FastAPI backend + React frontend in one repository, separated by clear module
boundaries. No microservices, no vector database, no message broker initially.

## AD-002 — Local development database is Supabase Postgres
**Status:** accepted (2026-10-24)
Development and production both use the Supabase-hosted PostgreSQL instance
rather than Docker/local Postgres. Consequences:
- The connection string is a secret and lives only in `backend/.env`.
- Alembic migrations run against Supabase (use the direct connection or the
  session pooler, not the transaction pooler, to avoid prepared-statement issues).
- Tests that need a database use a dedicated schema/database, never production data.

## AD-003 — Supabase Auth verified with JWKS
**Status:** accepted (2026-10-24)
The frontend signs users in with Supabase Auth. The backend verifies the access
token's signature against the project's JWKS endpoint (asymmetric keys), then
checks issuer, audience, and expiry. The frontend is never trusted to state who
the user is. `sub` (the Supabase user id) is the user's identity key.

## AD-004 — AI cannot control the journey
**Status:** accepted (Architecture V1.0)
Gemini sits behind a `AIProvider` interface and only produces text. Unlocking,
sequencing, prerequisites, task completion, and authorization are computed by
backend services from the database. AI output is stored and labeled separately
from Scripture.

## AD-005 — Curriculum content is not available yet
**Status:** open (2026-10-24)
The 387 Walks / 15 Parts content does not exist in a usable data format. The
schema and UI will be built against a small set of seed Walks. A content
ingestion plan is required before launch.

## AD-006 — Reminder delivery is at-least-once with idempotency
**Status:** accepted, to implement in Stage 8
Reminder jobs are claimed atomically in the database, retried with backoff, and
recorded in a delivery table with a unique key. "Scheduled" never means
"delivered".

## AD-007 — Repository location
**Status:** accepted (2026-10-24)
The project lives at `C:\dev\Walk_with_God`, outside OneDrive, to avoid file
lock and sync problems with `.git`, `.venv`, and `node_modules`.
