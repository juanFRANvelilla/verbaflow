"""verbaflow initial schema: users, languages, vocabulary_entries

Revision ID: 0001
Revises:
Create Date: 2026-03-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "languages",
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "vocabulary_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("translation", sa.Text(), nullable=False),
        sa.Column("example_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["language_code"], ["languages.code"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "language_code", "text", name="uq_vocab_user_lang_text"),
    )
    op.create_index("ix_vocabulary_entries_user_id", "vocabulary_entries", ["user_id"])
    op.create_index("ix_vocabulary_entries_language_code", "vocabulary_entries", ["language_code"])

    op.execute(
        sa.text(
            "INSERT INTO languages (code, name, enabled) VALUES ('en', 'English', true) "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO users (id, display_name) VALUES "
            "('00000000-0000-4000-8000-000000000001', 'default') ON CONFLICT (id) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_vocabulary_entries_language_code", table_name="vocabulary_entries")
    op.drop_index("ix_vocabulary_entries_user_id", table_name="vocabulary_entries")
    op.drop_table("vocabulary_entries")
    op.drop_table("languages")
    op.drop_table("users")