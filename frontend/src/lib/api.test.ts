import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from './api'

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
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
