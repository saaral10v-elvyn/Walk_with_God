import { act, render, screen } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../lib/api'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './context'

const mocks = vi.hoisted(() => {
  const listeners: Array<(event: string, session: unknown) => void> = []
  return {
    listeners,
    getSession: vi.fn(),
    onAuthStateChange: vi.fn(
      (callback: (event: string, session: unknown) => void) => {
        listeners.push(callback)
        return { data: { subscription: { unsubscribe: vi.fn() } } }
      },
    ),
    signInWithPassword: vi.fn(),
    signInWithOAuth: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
  }
})

vi.mock('../lib/supabase', () => ({
  isSupabaseConfigured: true,
  supabase: {
    auth: {
      getSession: mocks.getSession,
      onAuthStateChange: mocks.onAuthStateChange,
      signInWithPassword: mocks.signInWithPassword,
      signInWithOAuth: mocks.signInWithOAuth,
      signUp: mocks.signUp,
      signOut: mocks.signOut,
    },
  },
}))

function Consumer() {
  const { user, loading, signOut, signInWithGoogle } = useAuth()

  return (
    <div>
      <p>{loading ? 'loading' : (user?.email ?? 'signed out')}</p>
      <button type="button" onClick={() => void signOut()}>
        sign out
      </button>
      <button type="button" onClick={() => void signInWithGoogle()}>
        google
      </button>
    </div>
  )
}

function sessionFor(email: string): Session {
  return {
    access_token: 'access-token',
    refresh_token: 'refresh-token',
    expires_in: 3600,
    token_type: 'bearer',
    user: { id: 'user-id', email },
  } as unknown as Session
}

function renderProvider() {
  return render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  )
}

beforeEach(() => {
  mocks.listeners.length = 0
  mocks.getSession.mockReset()
  mocks.onAuthStateChange.mockClear()
  mocks.signInWithOAuth.mockReset()
  mocks.signOut.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('AuthProvider', () => {
  it('restores a stored session', async () => {
    mocks.getSession.mockResolvedValue({
      data: { session: sessionFor('reader@example.com') },
    })

    renderProvider()

    expect(await screen.findByText('reader@example.com')).toBeInTheDocument()
  })

  it('shows signed out when there is no stored session', async () => {
    mocks.getSession.mockResolvedValue({ data: { session: null } })

    renderProvider()

    expect(await screen.findByText('signed out')).toBeInTheDocument()
  })

  it('follows auth state changes', async () => {
    mocks.getSession.mockResolvedValue({ data: { session: null } })
    mocks.signOut.mockImplementation(async () => {
      for (const listener of mocks.listeners) listener('SIGNED_OUT', null)
      return { error: null }
    })

    renderProvider()
    await screen.findByText('signed out')

    act(() => {
      for (const listener of mocks.listeners) {
        listener('SIGNED_IN', sessionFor('reader@example.com'))
      }
    })
    expect(screen.getByText('reader@example.com')).toBeInTheDocument()

    act(() => {
      screen.getByRole('button', { name: 'sign out' }).click()
    })
    expect(await screen.findByText('signed out')).toBeInTheDocument()
  })

  it('starts Google sign-in through Supabase OAuth', async () => {
    mocks.getSession.mockResolvedValue({ data: { session: null } })
    mocks.signInWithOAuth.mockResolvedValue({
      data: { provider: 'google' },
      error: null,
    })

    renderProvider()
    await screen.findByText('signed out')

    await act(async () => {
      screen.getByRole('button', { name: 'google' }).click()
    })

    expect(mocks.signInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/account` },
    })
  })

  it('supplies the current access token to API calls', async () => {
    mocks.getSession.mockResolvedValue({
      data: { session: sessionFor('reader@example.com') },
    })
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    })
    vi.stubGlobal('fetch', fetchMock)

    renderProvider()
    await screen.findByText('reader@example.com')

    await api.me()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer access-token',
        }),
      }),
    )
  })
})
