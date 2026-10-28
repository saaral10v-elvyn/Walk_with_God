"""Database connectivity smoke test.

Prints only a success marker or a sanitized error category. It never prints the
connection string, credentials, SQL, or raw exception messages.
"""

import asyncio
import sys
from pathlib import Path

# Allow running as `uv run python scripts/db_check.py` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import (  # noqa: E402
    DatabaseNotConfiguredError,
    create_engine_from_settings,
)


def categorize(error: BaseException) -> str:
    """Map an exception to a short category without exposing its message."""
    if isinstance(error, DatabaseNotConfiguredError):
        return "not_configured"

    name = type(error).__name__.lower()
    message = str(error).lower()

    if "password" in message or "authentication" in message or "invalidpassword" in name:
        return "authentication_failed"
    if "certificate" in message or "ssl" in message or "tls" in message:
        return "tls_error"
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if "getaddrinfo" in message or "name or service not known" in message or "nodename" in message:
        return "dns_failure"
    if "connection refused" in message or "connect call failed" in message:
        return "connection_refused"
    if "invalidcatalogname" in name or "does not exist" in message:
        return "database_not_found"
    return "unknown"


async def check() -> int:
    settings = get_settings()

    if settings.database_dsn is None:
        print("connection failed: not_configured")
        print("Add DATABASE_URL to backend/.env (see .env.example).")
        return 2

    try:
        engine = create_engine_from_settings(settings)
    except Exception as error:  # configuration/URL parsing problems
        print(f"connection failed: {categorize(error)}")
        return 1

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as error:
        print(f"connection failed: {categorize(error)}")
        return 1
    finally:
        await engine.dispose()

    print("connected")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
