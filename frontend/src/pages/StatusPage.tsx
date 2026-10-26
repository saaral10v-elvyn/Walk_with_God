import { useEffect, useState } from 'react'

import { api, type HealthResponse } from '../lib/api'

type StatusState =
  | { phase: 'loading' }
  | { phase: 'ok'; data: HealthResponse }
  | { phase: 'error'; message: string }

export function StatusPage() {
  const [state, setState] = useState<StatusState>({ phase: 'loading' })

  useEffect(() => {
    let cancelled = false

    api
      .health()
      .then((data) => {
        if (!cancelled) setState({ phase: 'ok', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            phase: 'error',
            message:
              error instanceof Error
                ? error.message
                : 'An unexpected error occurred.',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="max-w-2xl">
      <h1 className="font-serif text-3xl">API status</h1>
      <p className="mt-3 text-muted">
        This page calls the FastAPI backend through the development proxy at{' '}
        <code className="rounded bg-sand px-1.5 py-0.5 text-sm">
          /api/v1/health
        </code>
        .
      </p>

      <div className="mt-8" aria-live="polite">
        {state.phase === 'loading' && (
          <p className="text-muted" role="status">
            Checking the server…
          </p>
        )}

        {state.phase === 'ok' && (
          <div className="rounded-xl border border-evergreen/30 bg-evergreen/5 p-6">
            <p className="font-medium text-evergreen">Server is healthy</p>
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between gap-6">
                <dt className="text-muted">Status</dt>
                <dd className="font-mono">{state.data.status}</dd>
              </div>
              <div className="flex justify-between gap-6">
                <dt className="text-muted">Version</dt>
                <dd className="font-mono">{state.data.version}</dd>
              </div>
              <div className="flex justify-between gap-6">
                <dt className="text-muted">Environment</dt>
                <dd className="font-mono">{state.data.environment}</dd>
              </div>
            </dl>
          </div>
        )}

        {state.phase === 'error' && (
          <div
            role="alert"
            className="rounded-xl border border-red-300 bg-red-50 p-6 text-red-800"
          >
            <p className="font-medium">The server could not be reached</p>
            <p className="mt-1 text-sm">{state.message}</p>
            <p className="mt-3 text-sm">
              Start it with{' '}
              <code className="rounded bg-white/60 px-1.5 py-0.5">
                cd backend; uv run uvicorn app.main:app --reload
              </code>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
