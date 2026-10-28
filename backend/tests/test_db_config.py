import ssl

import pytest

from app.core.config import Settings
from app.db.session import (
    DatabaseNotConfiguredError,
    build_engine_url,
    build_ssl_context,
)


def test_engine_url_upgrades_plain_postgres_scheme() -> None:
    settings = Settings(database_url="postgresql://user:secret@db.example.com:5432/postgres")

    url = build_engine_url(settings)

    assert url.drivername == "postgresql+asyncpg"
    assert url.database == "postgres"


def test_engine_url_removes_ssl_query_parameters() -> None:
    settings = Settings(
        database_url=(
            "postgresql://user:secret@db.example.com:5432/postgres?sslmode=require&ssl=require"
        )
    )

    assert build_engine_url(settings).query == {}


def test_engine_url_requires_database_url() -> None:
    with pytest.raises(DatabaseNotConfiguredError):
        build_engine_url(Settings(database_url=None))


def test_engine_url_rejects_other_drivers() -> None:
    settings = Settings(database_url="mysql://user:secret@db.example.com/app")

    with pytest.raises(DatabaseNotConfiguredError):
        build_engine_url(settings)


def test_settings_never_reveal_the_password() -> None:
    settings = Settings(database_url="postgresql://user:supersecret@db.example.com/postgres")

    assert "supersecret" not in repr(settings)
    assert "supersecret" not in str(settings.database_url)


def test_ssl_require_encrypts_without_verifying_identity() -> None:
    context = build_ssl_context(Settings(db_ssl_mode="require"))

    assert context.verify_mode == ssl.CERT_NONE
    assert context.check_hostname is False


def test_ssl_verify_full_needs_a_ca_file() -> None:
    with pytest.raises(DatabaseNotConfiguredError):
        build_ssl_context(Settings(db_ssl_mode="verify-full", db_ssl_ca_file=None))
