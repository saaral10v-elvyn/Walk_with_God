import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ProtectedRoute } from './ProtectedRoute'
import { useAuth, type AuthContextValue } from './context'

vi.mock('./context', () => ({
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
}

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/account']}>
      <Routes>
        <Route path="/login" element={<p>login page</p>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/account" element={<p>account page</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('shows a status message while the session is restored', () => {
    mockAuth({ loading: true })

    renderProtectedRoute()

    expect(screen.getByRole('status')).toHaveTextContent(
      'Checking your session',
    )
  })

  it('redirects signed-out visitors to the login page', () => {
    mockAuth()

    renderProtectedRoute()

    expect(screen.getByText('login page')).toBeInTheDocument()
  })

  it('renders the protected page for a signed-in user', () => {
    mockAuth({
      user: { email: 'reader@example.com' } as unknown as AuthContextValue['user'],
    })

    renderProtectedRoute()

    expect(screen.getByText('account page')).toBeInTheDocument()
  })
})
