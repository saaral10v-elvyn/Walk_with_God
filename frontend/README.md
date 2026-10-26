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
  main.tsx          React root + BrowserRouter
  App.tsx           route table
  components/       shared UI (Layout)
  pages/            Home, Status, NotFound
  lib/api.ts        typed fetch client + ApiError
  test/setup.ts     Vitest + Testing Library setup
  index.css         Tailwind import and design tokens
```

## Conventions

- All backend calls go through `src/lib/api.ts`; never call `fetch` in components.
- API errors are shown with their backend `message` and `code`.
- Design tokens (colours, fonts) live in `src/index.css` under `@theme`.
- Accessibility: semantic landmarks, skip link, visible focus, `aria-live` for async state.
