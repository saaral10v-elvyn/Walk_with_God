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

## AD-008 — Supabase TLS defaults to `require`, with `verify-full` available
**Status:** accepted (2026-10-27)
The shared pooler presents a certificate signed by a private Supabase CA, which
public trust stores reject. Supabase's documented default is `sslmode=require`:
traffic is encrypted, but the server identity is not verified. `DB_SSL_MODE`
therefore defaults to `require`. Full verification is supported by downloading
the project root certificate from the Supabase dashboard, setting
`DB_SSL_CA_FILE`, and switching to `verify-full`.

## AD-009 — Portable enums and explicit constraint names
**Status:** accepted (2026-10-27)
Status/section values are stored as `VARCHAR` with a `CHECK` constraint instead
of native PostgreSQL enums, because altering native enums is awkward in
migrations. A metadata naming convention gives every constraint a predictable
name, keeping Alembic diffs stable.

## AD-010 — User data is keyed by the Supabase user id
**Status:** accepted (2026-10-27)
`users.id` is the JWT `sub` UUID. No passwords or refresh tokens are stored in
the application database. Every user-owned table carries `user_id` with
`ON DELETE CASCADE`; authorization is enforced server-side in the service layer.

## AD-011 — Access tokens are verified locally against JWKS
**Status:** accepted (2026-10-27)
The backend never calls Supabase Auth to validate a request. It caches the
project's public keys (one hour by default), accepts only ES256/RS256, requires
`exp`, `iat`, `sub`, `aud`, and `iss`, and checks the audience and issuer. HMAC
and `none` are rejected so the legacy shared secret can never act as a signing
key. Unknown key ids trigger a throttled refresh to survive key rotation.
The `users` profile row is created lazily on the first authenticated request,
keyed by `sub`; no sign-up webhook is required.

## AD-012 — The browser keeps the Supabase session, the server keeps authority
**Status:** accepted (2026-10-27)
Supabase's browser client persists the session (localStorage by default) and
refreshes it automatically. That token is only a claim of identity: every
backend decision re-verifies it, and the browser is never allowed to state who
the user is or what they may access. If the stored token is missing, expired, or
tampered with, the API answers `401` and the UI returns to `/login`.
