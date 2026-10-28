import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { LoginPage } from './LoginPage'
import { useAuth, type AuthContextValue } from '../auth/context'
vi.mock('../auth/context', () => ({
  useAuth: vi.fn(),
}))

function mockAuth(overrides: Partial<AuthContextValue> = {}) {
  const value: AuthContextValue = {
    session: null,
    user: null,
    loading: false,
    configured: true,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signInWithGoogle: vi.fn(),
    signOut: vi.fn(),
    ...overrides,
  }
  vi.mocked(useAuth).mockReturnValue(value)
  return value
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/account" element={<p>account page</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function fillCredentials() {
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'reader@example.com' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'secret123' },
  })
}

describe('LoginPage', () => {
  afterEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('signs in and continues to the account page', async () => {
    const auth = mockAuth()
    vi.mocked(auth.signIn).mockResolvedValue(undefined)

    renderLogin()
    fillCredentials()
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('account page')).toBeInTheDocument()
    expect(auth.signIn).toHaveBeenCalledWith('reader@example.com', 'secret123')
  })

  it('asks the user to confirm their email after signing up', async () => {
    const auth = mockAuth()
    vi.mocked(auth.signUp).mockResolvedValue({ needsEmailConfirmation: true })

    renderLogin()
    fireEvent.click(screen.getByRole('button', { name: 'Create an account' }))
    fillCredentials()
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(
      await screen.findByText(/Check your inbox to confirm/),
    ).toBeInTheDocument()
    expect(auth.signUp).toHaveBeenCalledWith(
      'reader@example.com',
      'secret123',
    )
  })

  it('shows a configuration notice and disables the form', () => {
    mockAuth({ configured: false })

    renderLogin()

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Authentication is not configured',
    )
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDisabled()
  })

  it('redirects an already signed-in visitor', () => {
    mockAuth({
      user: { email: 'reader@example.com' } as unknown as AuthContextValue['user'],
    })

    renderLogin()

    expect(screen.getByText('account page')).toBeInTheDocument()
  })

  it('keeps the password hidden until the toggle is used', () => {
    const auth = mockAuth()

    renderLogin()

    const password = screen.getByLabelText('Password')
    expect(password).toHaveAttribute('type', 'password')

    const show = screen.getByRole('button', { name: 'Show password' })
    // A toggle must never submit the form.
    expect(show).toHaveAttribute('type', 'button')

    fireEvent.click(show)

    expect(password).toHaveAttribute('type', 'text')
    const hide = screen.getByRole('button', { name: 'Hide password' })
    expect(hide).toHaveAttribute('aria-controls', 'password')

    fireEvent.click(hide)

    expect(password).toHaveAttribute('type', 'password')
    expect(
      screen.getByRole('button', { name: 'Show password' }),
    ).toBeInTheDocument()
    expect(auth.signIn).not.toHaveBeenCalled()
  })

  it('starts Google sign-in and disables both options while pending', async () => {
    const auth = mockAuth()
    vi.mocked(auth.signInWithGoogle).mockReturnValue(new Promise(() => {}))

    renderLogin()
    fireEvent.click(screen.getByRole('button', { name: 'Continue with Google' }))

    expect(auth.signInWithGoogle).toHaveBeenCalledTimes(1)
    expect(
      await screen.findByRole('button', { name: 'Redirecting to Google…' }),
    ).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDisabled()
  })

  it('shows an error when Google sign-in cannot start', async () => {
    const auth = mockAuth()
    vi.mocked(auth.signInWithGoogle).mockRejectedValue(
      new Error('Provider is not enabled'),
    )

    renderLogin()
    fireEvent.click(screen.getByRole('button', { name: 'Continue with Google' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Provider is not enabled',
    )
    expect(
      screen.getByRole('button', { name: 'Continue with Google' }),
    ).toBeEnabled()
  })

  it('explains a cancelled Google redirect and cleans the address bar', () => {
    mockAuth()
    window.history.replaceState(
      {},
      '',
      '/login?error=access_denied&error_description=User+denied',
    )

    renderLogin()

    expect(screen.getByRole('alert')).toHaveTextContent(/cancelled/i)
    expect(window.location.search).toBe('')
  })
})
