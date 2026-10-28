"""Application profile persistence for authenticated users."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import Identity
from app.db.models.user import UserProfile


class ProfileService:
    """Read and maintain the row in ``users`` that mirrors a Supabase account.

    The profile is created on first authenticated request, so sign-up needs no
    extra callback endpoint and no password data ever reaches this service.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, identity: Identity) -> UserProfile:
        profile = await self._session.get(UserProfile, identity.user_id)

        if profile is None:
            profile = UserProfile(
                id=identity.user_id,
                email=identity.email,
                display_name=identity.display_name,
            )
            self._session.add(profile)
            try:
                await self._session.commit()
            except IntegrityError:
                # A concurrent request created the same row first. Use theirs.
                await self._session.rollback()
                existing = await self._session.get(UserProfile, identity.user_id)
                if existing is None:
                    raise
                return existing
            await self._session.refresh(profile)
            return profile

        # Keep the mirrored email current without touching user-owned data.
        if identity.email and profile.email != identity.email:
            profile.email = identity.email
            await self._session.commit()
            await self._session.refresh(profile)

        return profile
