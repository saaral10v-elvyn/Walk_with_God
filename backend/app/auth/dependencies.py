"""FastAPI dependencies for authenticated requests."""

from __future__ import annotations

from fastapi import Depends, Request

from app.auth.errors import AuthError, AuthNotConfiguredError
from app.auth.jwks import JwksCache
from app.auth.tokens import Identity, verify_access_token
from app.core.config import Settings, get_settings

_jwks_cache: JwksCache | None = None
_jwks_cache_url: str | None = None


def get_jwks_cache(settings: Settings = Depends(get_settings)) -> JwksCache:
    """Return one shared JWKS cache per configured project URL.

    Tests override this dependency with a static key source.
    """
    global _jwks_cache, _jwks_cache_url

    url = settings.effective_jwks_url
    if not url:
        raise AuthNotConfiguredError()

    if _jwks_cache is None or _jwks_cache_url != url:
        _jwks_cache = JwksCache(
            url,
            ttl_seconds=settings.supabase_jwks_cache_seconds,
            timeout_seconds=settings.supabase_jwks_timeout_seconds,
        )
        _jwks_cache_url = url

    return _jwks_cache


def reset_jwks_cache() -> None:
    """Drop the cached key set (used by tests and after a config change)."""
    global _jwks_cache, _jwks_cache_url
    _jwks_cache = None
    _jwks_cache_url = None


def get_bearer_token(request: Request) -> str:
    """Extract a bearer token from the Authorization header."""
    header = request.headers.get("Authorization")
    if not header:
        raise AuthError()

    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError()

    return token.strip()


async def get_current_identity(
    token: str = Depends(get_bearer_token),
    keys: JwksCache = Depends(get_jwks_cache),
    settings: Settings = Depends(get_settings),
) -> Identity:
    """Resolve the verified caller, or fail with a 401."""
    return await verify_access_token(token, keys=keys, settings=settings)
