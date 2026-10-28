"""Enumerations shared by the ORM models and API schemas."""

from enum import StrEnum

from sqlalchemy import Enum


class WalkStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SectionType(StrEnum):
    MAIN_PASSAGES = "main_passages"
    BIBLE_HISTORY = "bible_history"
    WALKING_WITH_GOD = "walking_with_god"
    GODS_CONNECTIONS = "gods_connections"
    TREASURE_TO_KEEP = "treasure_to_keep"
    SHORT_WALK_PRAYER = "short_walk_prayer"


class SectionSource(StrEnum):
    AUTHORED = "authored"
    AI_ASSISTED = "ai_assisted"


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


def enum_type(enum_class: type[StrEnum], name: str, length: int = 32) -> Enum:
    """Portable enum column: VARCHAR + CHECK constraint instead of a native type.

    Native PostgreSQL enums are awkward to alter in migrations, so we store the
    readable value (``"published"``) as text with a CHECK constraint.
    """
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
