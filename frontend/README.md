# Walk with God — Frontend

React + TypeScript + Vite + Tailwind CSS v4.

## Local setup (Windows PowerShell)

```powershell
cd C:\dev\Walk_with_God\frontend
npm install
Copy-Item .env.example .env   # optional; defaults work
npm run dev                   # http://localhost:5173
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000`, so start the
backend first:

```powershell
cd ..\backend
uv run uvicorn app.main:app --reload
```

## Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Development server with hot reload |
| `npm test` | Run Vitest once |
| `npm run test:watch` | Vitest in watch mode |
| `npm run lint` | oxlint |
| `npm run build` | Type-check (`tsc -b`) and production build |

## Layout

```
src/
  main.tsx          React root + BrowserRouter + AuthProvider
  App.tsx           route table
  auth/             AuthProvider, useAuth, ProtectedRoute
  components/       shared UI (Layout)
  pages/            Home, Status, Login, Account, NotFound
  lib/api.ts        typed fetch client + ApiError + bearer token injection
  lib/supabase.ts   Supabase browser client (null when unconfigured)
  test/setup.ts     Vitest + Testing Library setup
  index.css         Tailwind import and design tokens
```

## Authentication

Sign-in uses Supabase Auth. Copy `.env.example` to `.env` and set the project
values (the anon key is public by design; never put a service-role key here):

```dotenv
VITE_SUPABASE_URL="https://YOUR_PROJECT_REF.supabase.co"
VITE_SUPABASE_ANON_KEY=""
```

`AuthProvider` restores the stored session, refreshes tokens, and feeds the
current access token to `lib/api.ts`, which adds the `Authorization` header.
`ProtectedRoute` sends signed-out visitors to `/login`; `/account` calls
`GET /api/v1/auth/me` to show the backend profile.

### Google sign-in

"Continue with Google" calls `supabase.auth.signInWithOAuth({ provider: 'google' })`
on the existing client and redirects back to `/account`. It only works once the
Google provider is enabled in the Supabase Dashboard (Authentication → Providers)
and the redirect URL is allow-listed (Authentication → URL Configuration), e.g.
`http://localhost:5173/account`. Until then the button reports a provider error.

If the variables are missing, the app still runs and the login page explains
what to add instead of crashing.

## Conventions

- All backend calls go through `src/lib/api.ts`; never call `fetch` in components.
- API errors are shown with their backend `message` and `code`.
- Design tokens (colours, fonts) live in `src/index.css` under `@theme`.
- Accessibility: semantic landmarks, skip link, visible focus, `aria-live` for async state.
