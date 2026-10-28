import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError, setAccessTokenProvider } from './api'

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
  setAccessTokenProvider(() => null)
})

describe('api.health', () => {
  it('returns the parsed health payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ status: 'ok', version: '0.1.0', environment: 'test' }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.health()).resolves.toEqual({
      status: 'ok',
      version: '0.1.0',
      environment: 'test',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/health',
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: 'application/json' }),
      }),
    )
  })

  it('turns the backend error envelope into an ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          { error: { code: 'not_found', message: 'Resource not found.' } },
          404,
        ),
      ),
    )

    const error = await api.health().catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 404,
      code: 'not_found',
      message: 'Resource not found.',
    })
  })

  it('wraps network failures in a friendly ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    )

    await expect(api.health()).rejects.toMatchObject({
      status: 0,
      code: 'network_error',
    })
  })
})

describe('api.me', () => {
  const profile = {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'reader@example.com',
    display_name: null,
    timezone: 'UTC',
    created_at: '2026-10-27T10:00:00Z',
    updated_at: '2026-10-27T10:00:00Z',
  }

  it('sends the current access token as a bearer token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(profile))
    vi.stubGlobal('fetch', fetchMock)
    setAccessTokenProvider(() => 'token-abc')

    await expect(api.me()).resolves.toEqual(profile)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer token-abc',
        }),
      }),
    )
  })

  it('omits the Authorization header when signed out', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(profile))
    vi.stubGlobal('fetch', fetchMock)

    await api.me()

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(init.headers).not.toHaveProperty('Authorization')
  })

  it('surfaces an expired session as an unauthorized ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: 'unauthorized',
              message: 'A valid sign-in token is required.',
            },
          },
          401,
        ),
      ),
    )

    await expect(api.me()).rejects.toMatchObject({
      status: 401,
      code: 'unauthorized',
    })
  })
})
