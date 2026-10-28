const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

export interface HealthResponse {
  status: 'ok'
  version: string
  environment: string
}

export interface UserProfile {
  id: string
  email: string | null
  display_name: string | null
  timezone: string
  created_at: string
  updated_at: string
}

type AccessTokenProvider = () => string | null

let getAccessToken: AccessTokenProvider = () => null

/**
 * Register the function that supplies the current Supabase access token.
 * `AuthProvider` keeps it up to date; tests can set a fixed value.
 */
export function setAccessTokenProvider(provider: AccessTokenProvider): void {
  getAccessToken = provider
}

interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
  }
}

/**
 * An error returned by the backend (or a network failure).
 * `status` is 0 when the server could not be reached at all.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, options: { status: number; code: string }) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken()

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiError(
      'Could not reach the server. Check that the API is running.',
      { status: 0, code: 'network_error' },
    )
  }

  if (!response.ok) {
    let code = 'http_error'
    let message = `Request failed with status ${response.status}.`

    // The backend always sends { error: { code, message } }.
    try {
      const body = (await response.json()) as ApiErrorBody
      if (body.error?.code) code = body.error.code
      if (body.error?.message) message = body.error.message
    } catch {
      // Non-JSON error body: keep the generic message.
    }

    throw new ApiError(message, { status: response.status, code })
  }

  return (await response.json()) as T
}

/** Every backend call goes through here so auth and errors stay consistent. */
export const api = {
  health: () => request<HealthResponse>('/v1/health'),
  me: () => request<UserProfile>('/v1/auth/me'),
}
