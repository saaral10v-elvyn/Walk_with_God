from sqlalchemy import UniqueConstraint

from app.db import models  # noqa: F401  (registers tables)
from app.db.base import Base
from app.db.models import SectionType

EXPECTED_TABLES = {
    "notes",
    "parts",
    "reflections",
    "task_completions",
    "time_sessions",
    "users",
    "walk_passages",
    "walk_progress",
    "walk_sections",
    "walks",
}

USER_OWNED_TABLES = {
    "notes",
    "reflections",
    "task_completions",
    "time_sessions",
    "walk_progress",
}


def test_metadata_contains_exactly_the_planned_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_walk_has_the_six_sections() -> None:
    assert [section.value for section in SectionType] == [
        "main_passages",
        "bible_history",
        "walking_with_god",
        "gods_connections",
        "treasure_to_keep",
        "short_walk_prayer",
    ]


def test_progress_is_unique_per_user_and_walk() -> None:
    table = Base.metadata.tables["walk_progress"]
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "user_walk" in unique_names


def test_user_owned_rows_are_deleted_with_the_user() -> None:
    for table_name in USER_OWNED_TABLES:
        table = Base.metadata.tables[table_name]
        user_foreign_keys = [
            foreign_key
            for foreign_key in table.foreign_keys
            if foreign_key.column.table.name == "users"
        ]

        assert user_foreign_keys, f"{table_name} must reference users"
        assert user_foreign_keys[0].ondelete == "CASCADE"


def test_sections_cascade_when_a_walk_is_deleted() -> None:
    table = Base.metadata.tables["walk_sections"]
    walk_foreign_keys = [
        foreign_key
        for foreign_key in table.foreign_keys
        if foreign_key.column.table.name == "walks"
    ]

    assert walk_foreign_keys[0].ondelete == "CASCADE"
