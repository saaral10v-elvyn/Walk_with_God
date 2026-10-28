"""Verification of Supabase access tokens."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import jwt

from app.auth.errors import AuthError, AuthNotConfiguredError
from app.auth.jwks import ALLOWED_ALGORITHMS, KeySource
from app.core.config import Settings

logger = logging.getLogger(__name__)

REQUIRED_CLAIMS = ("exp", "iat", "sub", "aud", "iss")


@dataclass(frozen=True, slots=True)
class Identity:
    """The authenticated caller, derived only from verified claims."""

    user_id: uuid.UUID
    email: str | None = None
    display_name: str | None = None
    claims: dict[str, Any] = field(default_factory=dict, repr=False)


def _display_name_from_claims(claims: dict[str, Any]) -> str | None:
    metadata = claims.get("user_metadata")
    if not isinstance(metadata, dict):
        return None
    for key in ("display_name", "full_name", "name"):
        candidate = metadata.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()[:120]
    return None


async def verify_access_token(
    token: str,
    *,
    keys: KeySource,
    settings: Settings,
) -> Identity:
    """Verify a bearer token and return the caller's identity.

    Raises ``AuthError`` for anything that is not a currently valid token.
    """
    if not settings.auth_configured:
        raise AuthNotConfiguredError()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise AuthError() from None

    algorithm = header.get("alg")
    kid = header.get("kid")
    if algorithm not in ALLOWED_ALGORITHMS or not isinstance(kid, str) or not kid:
        raise AuthError()

    key = await keys.get_key(kid)
    if key is None:
        raise AuthError()

    try:
        claims = jwt.decode(
            token,
            key=key.key,
            algorithms=[algorithm],
            audience=settings.supabase_jwt_audience,
            issuer=settings.effective_jwt_issuer,
            leeway=settings.supabase_jwt_leeway_seconds,
            options={"require": list(REQUIRED_CLAIMS)},
        )
    except jwt.PyJWTError as error:
        # Log the class name only: no token, claim values, or key material.
        logger.info("Rejected access token (%s).", type(error).__name__)
        raise AuthError() from None

    subject = claims.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except (TypeError, ValueError):
        logger.info("Rejected access token (invalid subject claim).")
        raise AuthError() from None

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        email = None

    return Identity(
        user_id=user_id,
        email=email,
        display_name=_display_name_from_claims(claims),
        claims=claims,
    )
