"""Curriculum: Parts, Walks, the six Walk sections, and passage references."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.models.enums import SectionSource, SectionType, WalkStatus, enum_type


class Part(TimestampMixin, Base):
    """One of the 15 Parts that organize the journey."""

    __tablename__ = "parts"
    __table_args__ = (CheckConstraint("position > 0", name="position_positive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    walks: Mapped[list[Walk]] = relationship(
        back_populates="part",
        order_by="Walk.position_in_part",
    )


class Walk(TimestampMixin, Base):
    """A single Walk in the fixed 387-Walk sequence."""

    __tablename__ = "walks"
    __table_args__ = (
        UniqueConstraint("part_id", "position_in_part", name="part_position"),
        CheckConstraint("position_in_part > 0", name="position_in_part_positive"),
        CheckConstraint("global_sequence > 0", name="global_sequence_positive"),
        CheckConstraint(
            "estimated_minutes IS NULL OR estimated_minutes > 0",
            name="estimated_minutes_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    part_id: Mapped[int] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position_in_part: Mapped[int] = mapped_column(Integer, nullable=False)
    # Absolute position in the journey (1..387), independent of Part layout.
    global_sequence: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[WalkStatus] = mapped_column(
        enum_type(WalkStatus, "walk_status"),
        nullable=False,
        default=WalkStatus.DRAFT,
        server_default=WalkStatus.DRAFT.value,
        index=True,
    )
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    part: Mapped[Part] = relationship(back_populates="walks")
    sections: Mapped[list[WalkSection]] = relationship(
        back_populates="walk",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WalkSection.position",
    )
    passages: Mapped[list[WalkPassage]] = relationship(
        back_populates="walk",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WalkPassage.position",
    )


class WalkSection(TimestampMixin, Base):
    """One of the six sections of a Walk.

    ``source`` records whether the text was authored by a human or drafted with
    AI assistance, so Scripture and AI-generated explanations stay separable.
    """

    __tablename__ = "walk_sections"
    __table_args__ = (
        UniqueConstraint("walk_id", "section_type", name="walk_section_type"),
        UniqueConstraint("walk_id", "position", name="walk_section_position"),
        CheckConstraint("position BETWEEN 1 AND 6", name="position_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    walk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_type: Mapped[SectionType] = mapped_column(
        enum_type(SectionType, "section_type", length=40),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[SectionSource] = mapped_column(
        enum_type(SectionSource, "section_source"),
        nullable=False,
        default=SectionSource.AUTHORED,
        server_default=SectionSource.AUTHORED.value,
    )

    walk: Mapped[Walk] = relationship(back_populates="sections")


class WalkPassage(Base):
    """A Scripture reference attached to a Walk.

    Verse text is imported separately (Stage 6) so original Scripture is never
    mixed with authored or AI-generated commentary.
    """

    __tablename__ = "walk_passages"
    __table_args__ = (
        UniqueConstraint(
            "walk_id",
            "translation",
            "reference",
            name="walk_translation_reference",
        ),
        CheckConstraint("position > 0", name="position_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    walk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("walks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference: Mapped[str] = mapped_column(String(120), nullable=False)
    translation: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WEB",
        server_default="WEB",
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    note: Mapped[str | None] = mapped_column(Text)

    walk: Mapped[Walk] = relationship(back_populates="passages")
