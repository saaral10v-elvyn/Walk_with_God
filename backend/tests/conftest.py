"""Shared pytest fixtures.

Tests talk to the real FastAPI app over HTTP semantics using HTTPX's
ASGI transport, so no network port is opened and the tests stay fast.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Run async tests on asyncio only (trio is not a project dependency)."""
    return "asyncio"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        debug=False,
        cors_origins="http://localhost:5173",
    )


@pytest.fixture
async def client(test_settings: Settings) -> AsyncClient:
    """An HTTP client bound to a fresh app instance."""
    app = create_app(test_settings)
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
