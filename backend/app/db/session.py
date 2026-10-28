"""Async engine and session management.

The engine is created lazily: the API can start and serve its health check
before a database is configured, but any endpoint that needs data fails with a
clear, non-secret error.
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when a database operation is attempted without DATABASE_URL."""


def build_engine_url(settings: Settings) -> URL:
    """Normalize the configured DSN for the asyncpg driver.

    Accepts the connection string exactly as Supabase shows it
    (``postgresql://...``) and upgrades the driver. Credentials are never
    logged; the returned URL is only handed to SQLAlchemy.
    """
    raw = settings.database_dsn
    if raw is None:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not configured. Add it to backend/.env (see .env.example)."
        )

    url = make_url(raw)

    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")
    elif url.drivername != "postgresql+asyncpg":
        raise DatabaseNotConfiguredError(
            "DATABASE_URL must use PostgreSQL (postgresql:// or postgresql+asyncpg://)."
        )

    # SSL is configured explicitly through connect_args, so remove any
    # ssl/sslmode query parameters to avoid duplicate keyword arguments.
    query = {key: value for key, value in url.query.items() if key not in {"ssl", "sslmode"}}
    url = url.set(query=query)

    if not url.database:
        url = url.set(database="postgres")

    return url


def build_ssl_context(settings: Settings) -> ssl.SSLContext:
    """TLS settings for Supabase.

    Supabase's shared pooler presents a certificate signed by a private
    Supabase CA, which public trust stores reject. Their documented default is
    ``sslmode=require``: the connection is encrypted, but the server identity is
    not verified. Set ``DB_SSL_MODE=verify-full`` and ``DB_SSL_CA_FILE`` to the
    root certificate downloaded from the Supabase dashboard for full
    verification.
    """
    if settings.db_ssl_mode == "verify-full":
        if not settings.db_ssl_ca_file:
            raise DatabaseNotConfiguredError(
                "DB_SSL_MODE=verify-full requires DB_SSL_CA_FILE pointing at the "
                "Supabase root certificate."
            )
        context = ssl.create_default_context(cafile=settings.db_ssl_ca_file)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context

    # Encryption without identity verification (equivalent to sslmode=require).
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def build_connect_args(settings: Settings) -> dict[str, Any]:
    """Connection options shared by every asyncpg connection."""
    return {"ssl": build_ssl_context(settings)}


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Build a new engine. Callers own its lifecycle."""
    return create_async_engine(
        build_engine_url(settings),
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_timeout=settings.db_pool_timeout_seconds,
        connect_args=build_connect_args(settings),
    )


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = create_engine_from_settings(get_settings())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a session and rolls back on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Close pooled connections (called on application shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
