import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/context'

type Mode = 'sign-in' | 'sign-up'

interface LocationState {
  from?: string
}

const GOOGLE_CANCELLED =
  'Google sign-in was cancelled. You can try again, or use your email and password.'
const GOOGLE_FAILED = 'Google sign-in could not be completed. Please try again.'

/**
 * Supabase reports OAuth failures as `error` parameters on the redirect URL.
 * Read only those keys — never tokens.
 */
function oauthErrorCode(): string | null {
  if (typeof window === 'undefined') return null
  const search = new URLSearchParams(window.location.search)
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  return search.get('error') ?? hash.get('error')
}

function readOAuthError(): string | null {
  const code = oauthErrorCode()
  if (!code) return null
  return code === 'access_denied' ? GOOGLE_CANCELLED : GOOGLE_FAILED
}

/**
 * Tidy the address bar after an OAuth failure so a refresh starts clean.
 * Only error keys are removed; session tokens are never touched.
 */
function clearOAuthErrorParams(): void {
  if (typeof window === 'undefined' || !oauthErrorCode()) return

  const url = new URL(window.location.href)
  for (const key of ['error', 'error_code', 'error_description']) {
    url.searchParams.delete(key)
  }
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const hashHasTokens = hash.has('access_token') || hash.has('refresh_token')
  if (!hashHasTokens) url.hash = ''

  window.history.replaceState({}, '', url.toString())
}

function GoogleMark() {
  return (
    <svg
      viewBox="0 0 18 18"
      className="h-[18px] w-[18px] shrink-0"
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="#4285F4"
        d="M17.64 9.2045c0-.6381-.0573-1.2518-.1636-1.8409H9v3.4814h4.8436c-.2086 1.125-.8427 2.0782-1.7959 2.7164v2.2581h2.9087c1.7018-1.5668 2.6836-3.874 2.6836-6.615z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.4673-.806 5.9564-2.1805l-2.9087-2.2581c-.8059.54-1.8368.8591-3.0477.8591-2.344 0-4.3282-1.5831-5.036-3.7104H.9573v2.3318C2.4382 15.9832 5.4818 18 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.71c-.18-.54-.2822-1.1168-.2822-1.71s.1023-1.17.2823-1.71V4.9582H.9573A8.9965 8.9965 0 0 0 0 9c0 1.4523.3477 2.8268.9573 4.0418L3.964 10.71z"
      />
      <path
        fill="#EA4335"
        d="M9 3.5795c1.3214 0 2.5077.4541 3.4405 1.346l2.5813-2.5814C13.4632.8918 11.4259 0 9 0 5.4818 0 2.4382 2.0168.9573 4.9582L3.964 7.29C4.6718 5.1627 6.656 3.5795 9 3.5795z"
      />
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M2.25 12S5.75 5.25 12 5.25 21.75 12 21.75 12 18.25 18.75 12 18.75 2.25 12 2.25 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function EyeOffIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M3 3l18 18" />
      <path d="M10.6 6.2A9.9 9.9 0 0 1 12 6.1c6.25 0 9.75 6 9.75 6a17.4 17.4 0 0 1-3.4 3.9" />
      <path d="M6.3 7.9A17.5 17.5 0 0 0 2.25 12.1s3.5 6 9.75 6a9.7 9.7 0 0 0 4.1-.9" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
    </svg>
  )
}

export function LoginPage() {
  const { user, loading, configured, signIn, signUp, signInWithGoogle } =
    useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [mode, setMode] = useState<Mode>('sign-in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [googleBusy, setGoogleBusy] = useState(false)
  const [error, setError] = useState<string | null>(readOAuthError)
  const [notice, setNotice] = useState<string | null>(null)

  const from = (location.state as LocationState | null)?.from ?? '/account'
  const anyBusy = busy || googleBusy

  // Remove OAuth failure parameters from the URL once they are displayed.
  useEffect(() => {
    clearOAuthErrorParams()
  }, [])

  // If the browser restores this page from cache after a redirect, the
  // "redirecting" state would otherwise stick forever.
  useEffect(() => {
    if (!googleBusy) return
    const reset = () => setGoogleBusy(false)
    window.addEventListener('pageshow', reset)
    return () => window.removeEventListener('pageshow', reset)
  }, [googleBusy])

  if (!loading && user) {
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    setBusy(true)

    try {
      if (mode === 'sign-in') {
        await signIn(email, password)
        navigate(from, { replace: true })
      } else {
        const result = await signUp(email, password)
        if (result.needsEmailConfirmation) {
          setMode('sign-in')
          setNotice(
            'Check your inbox to confirm your email address, then sign in.',
          )
        } else {
          navigate(from, { replace: true })
        }
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function handleGoogleSignIn() {
    setError(null)
    setNotice(null)
    setGoogleBusy(true)

    try {
      await signInWithGoogle()
      // On success the browser navigates to Google; stay busy until it does.
    } catch (caught) {
      setError(
        caught instanceof Error && caught.message
          ? caught.message
          : GOOGLE_FAILED,
      )
      setGoogleBusy(false)
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="font-serif text-3xl">
        {mode === 'sign-in' ? 'Sign in' : 'Create an account'}
      </h1>
      <p className="mt-3 text-muted">
        Your progress, notes, and reflections stay tied to your account.
      </p>

      {!configured && (
        <div
          role="alert"
          className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"
        >
          <p className="font-medium">Authentication is not configured yet.</p>
          <p className="mt-1">
            Add <code className="rounded bg-white/70 px-1">VITE_SUPABASE_URL</code>{' '}
            and{' '}
            <code className="rounded bg-white/70 px-1">
              VITE_SUPABASE_ANON_KEY
            </code>{' '}
            to <code className="rounded bg-white/70 px-1">frontend/.env</code>,
            then restart the dev server.
          </p>
        </div>
      )}

      <button
        type="button"
        onClick={() => void handleGoogleSignIn()}
        disabled={anyBusy || !configured}
        className="mt-8 flex w-full items-center justify-center gap-3 rounded-full border border-sand bg-white/70 px-6 py-3 font-medium transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        <GoogleMark />
        <span>
          {googleBusy ? 'Redirecting to Google…' : 'Continue with Google'}
        </span>
      </button>

      <div className="mt-6 flex items-center gap-4 text-sm text-muted">
        <span aria-hidden="true" className="h-px flex-1 bg-sand" />
        <span>or</span>
        <span aria-hidden="true" className="h-px flex-1 bg-sand" />
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5" noValidate>
        <div>
          <label htmlFor="email" className="block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1.5 w-full rounded-lg border border-sand bg-white/70 px-3 py-2"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <div className="relative mt-1.5">
            <input
              id="password"
              name="password"
              type={passwordVisible ? 'text' : 'password'}
              autoComplete={
                mode === 'sign-in' ? 'current-password' : 'new-password'
              }
              required
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-sand bg-white/70 px-3 py-2 pr-12"
            />
            <button
              type="button"
              onClick={() => setPasswordVisible((visible) => !visible)}
              aria-label={passwordVisible ? 'Hide password' : 'Show password'}
              aria-controls="password"
              className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg text-muted transition-colors hover:text-ink"
            >
              {passwordVisible ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          </div>
          {mode === 'sign-up' && (
            <p className="mt-1 text-xs text-muted">At least 6 characters.</p>
          )}
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {error}
          </p>
        )}

        {notice && (
          <p
            role="status"
            className="rounded-lg border border-evergreen/30 bg-evergreen/5 px-3 py-2 text-sm text-evergreen"
          >
            {notice}
          </p>
        )}

        <button
          type="submit"
          disabled={anyBusy || !configured}
          className="w-full rounded-full bg-evergreen px-6 py-3 font-medium text-parchment transition-colors hover:bg-evergreen-dark disabled:cursor-not-allowed disabled:opacity-60"
        >
          {busy
            ? 'Please wait…'
            : mode === 'sign-in'
              ? 'Sign in'
              : 'Create account'}
        </button>
      </form>

      <p className="mt-6 text-sm text-muted">
        {mode === 'sign-in' ? 'New here?' : 'Already have an account?'}{' '}
        <button
          type="button"
          className="font-medium text-evergreen underline underline-offset-2"
          onClick={() => {
            setMode(mode === 'sign-in' ? 'sign-up' : 'sign-in')
            setError(null)
            setNotice(null)
          }}
        >
          {mode === 'sign-in' ? 'Create an account' : 'Sign in instead'}
        </button>
      </p>
    </div>
  )
}
