"""Authentication endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_identity
from app.auth.service import ProfileService
from app.auth.tokens import Identity
from app.db.models.user import UserProfile
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


class UserProfileResponse(BaseModel):
    """The signed-in user's application profile (never a token or secret)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    display_name: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


def get_profile_service(session: AsyncSession = Depends(get_db_session)) -> ProfileService:
    """Provide the profile service (overridden in tests)."""
    return ProfileService(session)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Current user profile",
    description=(
        "Verifies the Supabase access token and returns the caller's profile, "
        "creating it on first sign-in. Only the token's own user is ever read."
    ),
)
async def read_current_user(
    identity: Identity = Depends(get_current_identity),
    profiles: ProfileService = Depends(get_profile_service),
) -> UserProfile:
    return await profiles.get_or_create(identity)
