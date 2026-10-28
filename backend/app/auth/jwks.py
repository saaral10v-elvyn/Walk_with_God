"""Cached access to the Supabase JSON Web Key Set (JWKS).

Supabase signs access tokens with asymmetric keys (normally ES256) and
publishes the public halves at ``/auth/v1/.well-known/jwks.json``. Keys are
cached in memory and refreshed when they expire or when a token references an
unknown key id (for example right after a key rotation).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx
import jwt

from app.auth.errors import AuthUnavailableError

logger = logging.getLogger(__name__)

JwksFetcher = Callable[[str], Awaitable[dict[str, Any]]]

# Only asymmetric algorithms are accepted. Never allow "none" or HMAC
# algorithms: a shared secret must not be usable as a signing key here.
ALLOWED_ALGORITHMS = frozenset({"ES256", "RS256"})


class KeySource(Protocol):
    """Minimal interface the token verifier needs (easy to fake in tests)."""

    async def get_key(self, kid: str) -> jwt.PyJWK | None:
        """Return the parsed public key for ``kid``, or None if unknown."""


async def fetch_jwks(url: str, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Download the JWKS document. Raises on network or HTTP errors."""
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("JWKS payload is not an object")
    return payload


class JwksCache:
    """In-memory JWKS cache with a TTL and a refresh throttle."""

    def __init__(
        self,
        url: str,
        *,
        fetcher: JwksFetcher = fetch_jwks,
        ttl_seconds: int = 3600,
        min_refresh_seconds: int = 30,
        timeout_seconds: float = 5.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = url
        self._fetcher = fetcher
        self._ttl_seconds = ttl_seconds
        self._min_refresh_seconds = min_refresh_seconds
        self._timeout_seconds = timeout_seconds
        self._clock = clock
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float | None = None
        self._last_attempt_at: float | None = None
        self._lock = asyncio.Lock()

    async def get_key(self, kid: str) -> jwt.PyJWK | None:
        """Return a cached key, refreshing the set when needed."""
        if not kid:
            return None

        async with self._lock:
            # After a failed fetch, wait out the throttle instead of calling
            # the endpoint again on every request.
            if (
                self._fetched_at is None
                and self._last_attempt_at is not None
                and self._clock() - self._last_attempt_at < self._min_refresh_seconds
            ):
                raise AuthUnavailableError()

            if self._needs_refresh(kid):
                await self._refresh()
            return self._keys.get(kid)

    def _needs_refresh(self, kid: str) -> bool:
        if self._fetched_at is None:
            return True
        if kid in self._keys:
            return self._clock() - self._fetched_at >= self._ttl_seconds
        # Unknown kid: a rotation may have happened. Refresh, but not more
        # often than the throttle allows (prevents hammering the endpoint).
        return self._clock() - self._fetched_at >= self._min_refresh_seconds

    async def _refresh(self) -> None:
        self._last_attempt_at = self._clock()
        try:
            payload = await self._fetcher_with_timeout()
        except Exception as error:  # noqa: BLE001 - mapped to a safe error below
            logger.warning("JWKS fetch failed (%s).", type(error).__name__)
            raise AuthUnavailableError() from None

        keys: dict[str, jwt.PyJWK] = {}
        for jwk in payload.get("keys", []):
            if not isinstance(jwk, dict):
                continue
            kid = jwk.get("kid")
            algorithm = jwk.get("alg")
            if not isinstance(kid, str) or algorithm not in ALLOWED_ALGORITHMS:
                continue
            try:
                keys[kid] = jwt.PyJWK(jwk, algorithm=algorithm)
            except (jwt.PyJWTError, ValueError, KeyError):
                # Skip keys this runtime cannot use instead of failing every
                # request because one key in the set is unusual.
                logger.warning("Ignoring unusable JWKS key %r.", kid)

        self._keys = keys
        self._fetched_at = self._clock()

    async def _fetcher_with_timeout(self) -> dict[str, Any]:
        if self._fetcher is fetch_jwks:
            return await fetch_jwks(self._url, timeout_seconds=self._timeout_seconds)
        return await asyncio.wait_for(
            self._fetcher(self._url),
            timeout=self._timeout_seconds,
        )
