"""ORM models. Importing this package registers every table on ``Base.metadata``."""

from app.db.models.curriculum import Part, Walk, WalkPassage, WalkSection
from app.db.models.engagement import (
    Note,
    Reflection,
    TaskCompletion,
    TimeSession,
    WalkProgress,
)
from app.db.models.enums import (
    ProgressStatus,
    SectionSource,
    SectionType,
    WalkStatus,
)
from app.db.models.user import UserProfile

__all__ = [
    "Note",
    "Part",
    "ProgressStatus",
    "Reflection",
    "SectionSource",
    "SectionType",
    "TaskCompletion",
    "TimeSession",
    "UserProfile",
    "Walk",
    "WalkPassage",
    "WalkProgress",
    "WalkSection",
    "WalkStatus",
]
