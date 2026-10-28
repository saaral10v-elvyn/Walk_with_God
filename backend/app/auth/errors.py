"""Authentication failures, expressed in the shared error envelope."""

from fastapi import status

from app.core.errors import AppError


class AuthError(AppError):
    """The request did not carry a valid access token.

    The message is deliberately generic: it never reveals which check failed
    (signature, expiry, audience, issuer) so tokens cannot be probed.
    """

    def __init__(self) -> None:
        super().__init__(
            "A valid sign-in token is required.",
            code="unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthNotConfiguredError(AppError):
    """The server has no Supabase Auth settings, so it cannot verify tokens."""

    def __init__(self) -> None:
        super().__init__(
            "Authentication is not configured on the server.",
            code="auth_not_configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class AuthUnavailableError(AppError):
    """The signing keys could not be fetched, so verification cannot run."""

    def __init__(self) -> None:
        super().__init__(
            "Authentication is temporarily unavailable.",
            code="auth_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
