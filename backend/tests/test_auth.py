"""Authentication tests.

Tokens are signed with a locally generated EC key and verified against a static
JWKS, so no network call and no real Supabase project is involved.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from jwt.algorithms import ECAlgorithm
from sqlalchemy.exc import IntegrityError

from app.api.v1.auth import get_profile_service
from app.auth.dependencies import get_jwks_cache
from app.auth.errors import AuthUnavailableError
from app.auth.jwks import JwksCache
from app.auth.service import ProfileService
from app.auth.tokens import Identity
from app.core.config import Settings, get_settings
from app.db.models.user import UserProfile
from app.main import create_app

ISSUER = "https://project.supabase.co/auth/v1"
KID = "test-key-1"

PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
PUBLIC_JWK = ECAlgorithm.to_jwk(PRIVATE_KEY.public_key(), as_dict=True)
PUBLIC_JWK.update({"kid": KID, "alg": "ES256", "use": "sig"})

OTHER_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


class StaticKeys:
    """Key source with exactly one known key."""

    def __init__(self) -> None:
        self._key = jwt.PyJWK(PUBLIC_JWK, algorithm="ES256")

    async def get_key(self, kid: str) -> jwt.PyJWK | None:
        return self._key if kid == KID else None


def auth_settings() -> Settings:
    return Settings(
        environment="test",
        supabase_url="https://project.supabase.co",
        supabase_jwks_url=None,
        supabase_jwt_issuer=None,
        supabase_jwt_audience="authenticated",
    )


def make_claims(**overrides: object) -> dict[str, object]:
    now = int(time.time())
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "email": "reader@example.com",
        "aud": "authenticated",
        "iss": ISSUER,
        "iat": now,
        "exp": now + 300,
        "role": "authenticated",
    }
    claims.update(overrides)
    return claims


def sign(claims: dict[str, object], *, key: object = PRIVATE_KEY) -> str:
    return jwt.encode(claims, key, algorithm="ES256", headers={"kid": KID})


class FakeProfiles:
    def __init__(self, profile: SimpleNamespace) -> None:
        self.profile = profile

    async def get_or_create(self, identity: Identity) -> SimpleNamespace:
        assert identity.user_id == self.profile.id
        return self.profile


def make_profile(user_id: uuid.UUID, email: str | None = "reader@example.com") -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=user_id,
        email=email,
        display_name=None,
        timezone="UTC",
        created_at=now,
        updated_at=now,
    )


def build_app(profile: SimpleNamespace, settings: Settings | None = None) -> FastAPI:
    app = create_app(settings or auth_settings())
    active_settings = settings or auth_settings()
    app.dependency_overrides[get_settings] = lambda: active_settings
    app.dependency_overrides[get_jwks_cache] = StaticKeys
    app.dependency_overrides[get_profile_service] = lambda: FakeProfiles(profile)
    return app


async def request(app: FastAPI, *, authorization: str | None) -> Response:
    headers = {"Authorization": authorization} if authorization else {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/api/v1/auth/me", headers=headers)


@pytest.mark.anyio
async def test_valid_token_returns_the_callers_profile() -> None:
    user_id = uuid.uuid4()
    app = build_app(make_profile(user_id))

    response = await request(app, authorization=f"Bearer {sign(make_claims(sub=str(user_id)))}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user_id)
    assert body["email"] == "reader@example.com"
    assert body["timezone"] == "UTC"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "authorization",
    [None, "", "Basic abc", "Bearer", "Bearer not-a-jwt"],
)
async def test_missing_or_malformed_authorization_is_rejected(authorization: str | None) -> None:
    app = build_app(make_profile(uuid.uuid4()))

    response = await request(app, authorization=authorization)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.anyio
async def test_token_signed_by_another_key_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = jwt.encode(
        make_claims(),
        OTHER_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": KID},
    )

    response = await request(app, authorization=f"Bearer {token}")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_expired_token_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = sign(make_claims(exp=int(time.time()) - 3600))

    assert (await request(app, authorization=f"Bearer {token}")).status_code == 401


@pytest.mark.anyio
async def test_token_without_expiry_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    claims = make_claims()
    del claims["exp"]

    assert (await request(app, authorization=f"Bearer {sign(claims)}")).status_code == 401


@pytest.mark.anyio
async def test_wrong_audience_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = sign(make_claims(aud="another-app"))

    assert (await request(app, authorization=f"Bearer {token}")).status_code == 401


@pytest.mark.anyio
async def test_wrong_issuer_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = sign(make_claims(iss="https://evil.example.com/auth/v1"))

    assert (await request(app, authorization=f"Bearer {token}")).status_code == 401


@pytest.mark.anyio
async def test_unknown_key_id_is_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = jwt.encode(
        make_claims(),
        PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": "rotated-away"},
    )

    assert (await request(app, authorization=f"Bearer {token}")).status_code == 401


@pytest.mark.anyio
async def test_hmac_and_none_algorithms_are_rejected() -> None:
    app = build_app(make_profile(uuid.uuid4()))

    hmac_token = jwt.encode(
        make_claims(),
        "a-shared-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
        headers={"kid": KID},
    )
    none_token = jwt.encode(make_claims(), None, algorithm="none", headers={"kid": KID})

    assert (await request(app, authorization=f"Bearer {hmac_token}")).status_code == 401
    assert (await request(app, authorization=f"Bearer {none_token}")).status_code == 401


@pytest.mark.anyio
async def test_subject_must_be_a_uuid() -> None:
    app = build_app(make_profile(uuid.uuid4()))
    token = sign(make_claims(sub="not-a-uuid"))

    assert (await request(app, authorization=f"Bearer {token}")).status_code == 401


@pytest.mark.anyio
async def test_unconfigured_server_returns_503() -> None:
    settings = Settings(environment="test", supabase_url=None)
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings

    response = await request(app, authorization=f"Bearer {sign(make_claims())}")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_not_configured"


# --- JWKS cache behaviour -------------------------------------------------


@pytest.mark.anyio
async def test_jwks_cache_fetches_once_for_repeated_lookups() -> None:
    calls = 0

    async def fetcher(url: str) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"keys": [PUBLIC_JWK]}

    cache = JwksCache("https://project.supabase.co/jwks", fetcher=fetcher)

    assert await cache.get_key(KID) is not None
    assert await cache.get_key(KID) is not None
    assert calls == 1


@pytest.mark.anyio
async def test_jwks_cache_refreshes_for_an_unknown_key_after_throttle() -> None:
    now = [1000.0]
    calls = 0

    async def fetcher(url: str) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"keys": [PUBLIC_JWK]}

    cache = JwksCache(
        "https://project.supabase.co/jwks",
        fetcher=fetcher,
        min_refresh_seconds=30,
        clock=lambda: now[0],
    )

    await cache.get_key(KID)
    assert await cache.get_key("unknown") is None
    assert calls == 1

    now[0] += 31
    assert await cache.get_key("unknown") is None
    assert calls == 2


@pytest.mark.anyio
async def test_jwks_cache_maps_fetch_failures_to_a_safe_error() -> None:
    calls = 0

    async def fetcher(url: str) -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise RuntimeError("network down")

    now = [1000.0]
    cache = JwksCache(
        "https://project.supabase.co/jwks",
        fetcher=fetcher,
        min_refresh_seconds=30,
        clock=lambda: now[0],
    )

    with pytest.raises(AuthUnavailableError):
        await cache.get_key(KID)

    # A second request during the throttle fails fast instead of retrying.
    with pytest.raises(AuthUnavailableError):
        await cache.get_key(KID)
    assert calls == 1

    # Once the throttle elapses, a new attempt is allowed.
    now[0] += 31
    with pytest.raises(AuthUnavailableError):
        await cache.get_key(KID)
    assert calls == 2


@pytest.mark.anyio
async def test_jwks_cache_ignores_keys_with_disallowed_algorithms() -> None:
    async def fetcher(url: str) -> dict[str, object]:
        return {
            "keys": [
                {"kid": "hmac-key", "alg": "HS256", "kty": "oct", "k": "c2VjcmV0"},
                PUBLIC_JWK,
            ]
        }

    cache = JwksCache("https://project.supabase.co/jwks", fetcher=fetcher)

    assert await cache.get_key("hmac-key") is None
    assert await cache.get_key(KID) is not None


# --- Profile upsert -------------------------------------------------------


class FakeSession:
    def __init__(self, existing: UserProfile | None = None) -> None:
        self.rows = {existing.id: existing} if existing else {}
        self.added: list[UserProfile] = []
        self.commits = 0
        self.refreshes = 0

    async def get(self, model: object, primary_key: uuid.UUID) -> UserProfile | None:
        return self.rows.get(primary_key)

    def add(self, row: UserProfile) -> None:
        self.added.append(row)
        self.rows[row.id] = row

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, row: UserProfile) -> None:
        self.refreshes += 1

    async def rollback(self) -> None:
        self.rows.clear()


def identity_for(user_id: uuid.UUID, email: str | None = "new@example.com") -> Identity:
    return Identity(user_id=user_id, email=email, display_name="Reader")


@pytest.mark.anyio
async def test_profile_is_created_on_first_sign_in() -> None:
    session = FakeSession()
    user_id = uuid.uuid4()

    profile = await ProfileService(session).get_or_create(identity_for(user_id))  # type: ignore[arg-type]

    assert profile.id == user_id
    assert profile.email == "new@example.com"
    assert profile.display_name == "Reader"
    assert session.commits == 1


@pytest.mark.anyio
async def test_existing_profile_email_is_refreshed() -> None:
    user_id = uuid.uuid4()
    existing = UserProfile(id=user_id, email="old@example.com")
    session = FakeSession(existing)

    profile = await ProfileService(session).get_or_create(identity_for(user_id))  # type: ignore[arg-type]

    assert profile.email == "new@example.com"
    assert session.commits == 1


@pytest.mark.anyio
async def test_unchanged_profile_is_not_written() -> None:
    user_id = uuid.uuid4()
    existing = UserProfile(id=user_id, email="new@example.com")
    session = FakeSession(existing)

    await ProfileService(session).get_or_create(identity_for(user_id))  # type: ignore[arg-type]

    assert session.commits == 0


class RaceSession(FakeSession):
    """Simulates another request inserting the row between get and commit."""

    def __init__(self, existing: UserProfile) -> None:
        super().__init__()
        self.existing = existing
        self.calls = 0
        self.rolled_back = False

    async def get(self, model: object, primary_key: uuid.UUID) -> UserProfile | None:
        self.calls += 1
        return None if self.calls == 1 else self.existing

    async def commit(self) -> None:
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.mark.anyio
async def test_concurrent_first_sign_in_reuses_the_existing_row() -> None:
    user_id = uuid.uuid4()
    existing = UserProfile(id=user_id, email="new@example.com")
    session = RaceSession(existing)

    profile = await ProfileService(session).get_or_create(identity_for(user_id))  # type: ignore[arg-type]

    assert profile is existing
    assert session.rolled_back is True
