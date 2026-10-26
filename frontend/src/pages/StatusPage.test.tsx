import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { api } from '../lib/api'
import { StatusPage } from './StatusPage'

vi.mock('../lib/api', () => ({
  api: { health: vi.fn() },
}))

describe('StatusPage', () => {
  it('shows backend details once the health check succeeds', async () => {
    vi.mocked(api.health).mockResolvedValue({
      status: 'ok',
      version: '0.1.0',
      environment: 'local',
    })

    render(<StatusPage />)

    expect(await screen.findByText('Server is healthy')).toBeInTheDocument()
    expect(screen.getByText('0.1.0')).toBeInTheDocument()
    expect(screen.getByText('local')).toBeInTheDocument()
  })

  it('shows an alert when the API cannot be reached', async () => {
    vi.mocked(api.health).mockRejectedValue(
      new Error('Could not reach the server. Check that the API is running.'),
    )

    render(<StatusPage />)

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Could not reach the server')
  })
})
