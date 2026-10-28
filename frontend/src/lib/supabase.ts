import { createClient } from '@supabase/supabase-js'

// Only public values belong here. The anon key is designed to be shipped to
// the browser; Row Level Security and the backend remain the real guards.
const url = import.meta.env.VITE_SUPABASE_URL?.trim()
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim()

export const isSupabaseConfigured = Boolean(url && anonKey)

/**
 * The Supabase client, or null when the environment is not configured.
 * Keeping it nullable lets the app render a helpful message instead of
 * crashing during local development or tests.
 */
export const supabase =
  url && anonKey
    ? createClient(url, anonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      })
    : null
