"""Supabase access-token verification.

Supabase Auth issues the tokens; this package only verifies them against the
project's published JWKS. No password, refresh token, or signing secret is
stored or handled here.
"""
