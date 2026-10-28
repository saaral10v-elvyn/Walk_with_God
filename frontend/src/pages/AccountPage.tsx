import { useEffect, useState } from 'react'

import { useAuth } from '../auth/context'
import { api, ApiError, type UserProfile } from '../lib/api'

type ProfileState =
  | { phase: 'loading' }
  | { phase: 'ready'; profile: UserProfile }
  | { phase: 'error'; message: string }

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
}

export function AccountPage() {
  const { user, signOut } = useAuth()
  const [state, setState] = useState<ProfileState>({ phase: 'loading' })
  const [signingOut, setSigningOut] = useState(false)

  useEffect(() => {
    let cancelled = false

    api
      .me()
      .then((profile) => {
        if (!cancelled) setState({ phase: 'ready', profile })
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        const message =
          caught instanceof ApiError && caught.status === 401
            ? 'Your session has expired. Please sign in again.'
            : caught instanceof Error
              ? caught.message
              : 'Your profile could not be loaded.'
        setState({ phase: 'error', message })
      })

    return () => {
      cancelled = true
    }
  }, [])

  async function handleSignOut() {
    setSigningOut(true)
    try {
      await signOut()
    } catch {
      setSigningOut(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-serif text-3xl">Your account</h1>
      <p className="mt-3 text-muted">
        Signed in as {user?.email ?? 'a verified account'}.
      </p>

      <div className="mt-8" aria-live="polite">
        {state.phase === 'loading' && (
          <p className="text-muted" role="status">
            Loading your profile…
          </p>
        )}

        {state.phase === 'error' && (
          <div
            role="alert"
            className="rounded-xl border border-red-300 bg-red-50 p-5 text-red-800"
          >
            <p className="font-medium">Profile unavailable</p>
            <p className="mt-1 text-sm">{state.message}</p>
          </div>
        )}

        {state.phase === 'ready' && (
          <dl className="space-y-3 rounded-xl border border-sand bg-white/40 p-6 text-sm">
            <div className="flex flex-wrap justify-between gap-2">
              <dt className="text-muted">Email</dt>
              <dd>{state.profile.email ?? 'Not set'}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-2">
              <dt className="text-muted">Display name</dt>
              <dd>{state.profile.display_name ?? 'Not set'}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-2">
              <dt className="text-muted">Timezone</dt>
              <dd className="font-mono">{state.profile.timezone}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-2">
              <dt className="text-muted">Member since</dt>
              <dd>{formatDate(state.profile.created_at)}</dd>
            </div>
          </dl>
        )}
      </div>

      <button
        type="button"
        onClick={() => void handleSignOut()}
        disabled={signingOut}
        className="mt-8 rounded-full border border-evergreen px-5 py-2.5 text-sm font-medium text-evergreen transition-colors hover:bg-evergreen hover:text-parchment disabled:opacity-60"
      >
        {signingOut ? 'Signing out…' : 'Sign out'}
      </button>
    </div>
  )
}
