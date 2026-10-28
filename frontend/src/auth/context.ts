import { createContext, useContext } from 'react'
import type { Session, User } from '@supabase/supabase-js'

export interface SignUpResult {
  /** True when Supabase requires the user to confirm their email first. */
  needsEmailConfirmation: boolean
}

export interface AuthContextValue {
  session: Session | null
  user: User | null
  /** True while the stored session is being restored on page load. */
  loading: boolean
  /** False when VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are missing. */
  configured: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<SignUpResult>
  /**
   * Starts the Google OAuth flow. On success the browser leaves the page, so
   * the session arrives later through `onAuthStateChange`.
   */
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return value
}
