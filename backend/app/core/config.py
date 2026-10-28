"""Application configuration.

All settings are read from environment variables (and an optional ``.env``
file). Secrets must never be hard-coded or committed to Git.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the backend directory so `.env` is found no matter which directory a
# command (uvicorn, alembic, scripts) is started from.
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed application settings.

    Field names map to environment variables case-insensitively, so
    ``app_version`` is read from ``APP_VERSION``.
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Walk with God API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Comma-separated list, e.g. "http://localhost:5173,https://app.example.com".
    # A plain string avoids fragile JSON parsing in environment variables.
    cors_origins: str = "http://localhost:5173"

    # --- Database (Stage 3) ---
    # SecretStr prevents the value from appearing in logs, tracebacks or repr().
    database_url: SecretStr | None = None
    db_echo: bool = False
    # "require" = encrypted but no certificate verification (Supabase default
    # guidance). "verify-full" = encryption plus server identity verification;
    # requires db_ssl_ca_file pointing at the project's downloaded root CA.
    db_ssl_mode: Literal["require", "verify-full"] = "require"
    db_ssl_ca_file: str | None = None
    db_pool_size: int = Field(default=5, ge=1, le=20)
    db_max_overflow: int = Field(default=5, ge=0, le=20)
    db_pool_recycle_seconds: int = Field(default=1800, ge=60)
    db_pool_timeout_seconds: int = Field(default=30, ge=1)

    # --- Supabase Auth (Stage 4) ---
    # Project URL, e.g. https://abcdefgh.supabase.co. The JWKS URL and issuer
    # are derived from it unless set explicitly below.
    supabase_url: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"
    # Tolerated clock skew (seconds) when checking exp/iat/nbf.
    supabase_jwt_leeway_seconds: int = Field(default=30, ge=0, le=300)
    supabase_jwks_cache_seconds: int = Field(default=3600, ge=60)
    supabase_jwks_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a clean list of strings."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_dsn(self) -> str | None:
        """Return the raw connection string, or None when it is not configured.

        The value is still a secret: callers must not log or return it.
        """
        if self.database_url is None:
            return None
        value = self.database_url.get_secret_value().strip()
        return value or None

    @property
    def supabase_project_url(self) -> str | None:
        """Return the normalized Supabase project URL, or None."""
        if not self.supabase_url:
            return None
        value = self.supabase_url.strip().rstrip("/")
        return value or None

    @property
    def effective_jwks_url(self) -> str | None:
        """JWKS endpoint, derived from the project URL when not set explicitly."""
        if self.supabase_jwks_url:
            return self.supabase_jwks_url.strip() or None
        base = self.supabase_project_url
        return f"{base}/auth/v1/.well-known/jwks.json" if base else None

    @property
    def effective_jwt_issuer(self) -> str | None:
        """Expected ``iss`` claim, derived from the project URL when not set."""
        if self.supabase_jwt_issuer:
            return self.supabase_jwt_issuer.strip().rstrip("/") or None
        base = self.supabase_project_url
        return f"{base}/auth/v1" if base else None

    @property
    def auth_configured(self) -> bool:
        """True when token verification has everything it needs."""
        return bool(
            self.effective_jwks_url
            and self.effective_jwt_issuer
            and self.supabase_jwt_audience.strip()
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read the environment only once)."""
    return Settings()
