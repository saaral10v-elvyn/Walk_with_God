import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { Session } from '@supabase/supabase-js'

import { setAccessTokenProvider } from '../lib/api'
import { isSupabaseConfigured, supabase } from '../lib/supabase'
import {
  AuthContext,
  type AuthContextValue,
  type SignUpResult,
} from './context'

const NOT_CONFIGURED =
  'Authentication is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env.'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(isSupabaseConfigured)

  // The API client asks for the token at call time. Updating this ref in the
  // auth callbacks (not during render) keeps it current even when a child
  // effect fires before this provider's own effect.
  const sessionRef = useRef<Session | null>(null)

  useEffect(() => {
    if (!supabase) return

    let active = true

    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!active) return
        sessionRef.current = data.session
        setSession(data.session)
        setLoading(false)
      })
      .catch(() => {
        if (active) setLoading(false)
      })

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      sessionRef.current = nextSession
      setSession(nextSession)
      setLoading(false)
    })

    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [])

  // Every API call reads the latest token through this provider.
  useEffect(() => {
    setAccessTokenProvider(() => sessionRef.current?.access_token ?? null)
    return () => setAccessTokenProvider(() => null)
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    if (!supabase) throw new Error(NOT_CONFIGURED)
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw new Error(error.message)
    sessionRef.current = data.session
    setSession(data.session)
  }, [])

  const signUp = useCallback(
    async (email: string, password: string): Promise<SignUpResult> => {
      if (!supabase) throw new Error(NOT_CONFIGURED)
      const { data, error } = await supabase.auth.signUp({ email, password })
      if (error) throw new Error(error.message)
      sessionRef.current = data.session
      setSession(data.session)
      return { needsEmailConfirmation: !data.session }
    },
    [],
  )

  const signInWithGoogle = useCallback(async () => {
    if (!supabase) throw new Error(NOT_CONFIGURED)
    // The redirect target must be allow-listed in the Supabase Dashboard.
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/account` },
    })
    if (error) throw new Error(error.message)
  }, [])

  const signOut = useCallback(async () => {
    if (!supabase) throw new Error(NOT_CONFIGURED)
    const { error } = await supabase.auth.signOut()
    if (error) throw new Error(error.message)
    sessionRef.current = null
    setSession(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      loading,
      configured: isSupabaseConfigured,
      signIn,
      signUp,
      signInWithGoogle,
      signOut,
    }),
    [session, loading, signIn, signUp, signInWithGoogle, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
