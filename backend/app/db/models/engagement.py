"""User-owned records: progress, task completion, time, notes, reflections.

Every table here carries ``user_id`` so access can always be scoped to the
authenticated user. Authorization is enforced in the service layer; the
database guarantees referential integrity.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.models.enums import ProgressStatus, enum_type


class WalkProgress(TimestampMixin, Base):
    __tablename__ = "walk_progress"
    __table_args__ = (UniqueConstraint("user_id", "walk_id", name="user_walk"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    walk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ProgressStatus] = mapped_column(
        enum_type(ProgressStatus, "progress_status"),
        nullable=False,
        default=ProgressStatus.NOT_STARTED,
        server_default=ProgressStatus.NOT_STARTED.value,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskCompletion(Base):
    """A completed task inside a Walk (for example one section).

    A unique key per user/Walk/task makes completion idempotent: repeating a
    request cannot create duplicates.
    """

    __tablename__ = "task_completions"
    __table_args__ = (UniqueConstraint("user_id", "walk_id", "task_key", name="user_walk_task"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    walk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_key: Mapped[str] = mapped_column(String(80), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TimeSession(Base):
    """Time spent in the journey, measured in explicit sessions."""

    __tablename__ = "time_sessions"
    __table_args__ = (
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="duration_non_negative",
        ),
        Index("ix_time_sessions_user_started_at", "user_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    walk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)


class Note(TimestampMixin, Base):
    """A private note attached to a Walk (or to the journey in general)."""

    __tablename__ = "notes"
    __table_args__ = (Index("ix_notes_user_created_at", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    walk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=False)


class Reflection(TimestampMixin, Base):
    """A saved personal reflection, optionally tied to a Walk prompt."""

    __tablename__ = "reflections"
    __table_args__ = (Index("ix_reflections_user_created_at", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    walk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        index=True,
    )
    prompt_key: Mapped[str | None] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text, nullable=False)
