"""initial schema

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
    source_kind = sa.Enum("series", "book", "other", name="source_kind")
    vocab_kind = sa.Enum("word", "phrase", "phrasal_verb", "idiom", "other", name="vocab_kind")
    source_kind.create(op.get_bind(), checkfirst=True)
    vocab_kind.create(op.get_bind(), checkfirst=True)

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
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", source_kind, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sources_user_id", "sources", ["user_id"])

    op.create_table(
        "vocab_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_en", sa.Text(), nullable=False),
        sa.Column("kind", vocab_kind, nullable=False),
        sa.Column("translation_es", sa.Text(), nullable=False),
        sa.Column("example_en", sa.Text(), nullable=True),
        sa.Column("example_es", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("phonetic_hint", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("from_lookup_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "canonical_en", name="uq_vocab_user_canonical"),
    )
    op.create_index("ix_vocab_items_user_id", "vocab_items", ["user_id"])

    op.create_table(
        "lookup_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audio_duration_ms", sa.Integer(), nullable=True),
        sa.Column("stt_model", sa.String(length=64), nullable=True),
        sa.Column("llm_model", sa.String(length=128), nullable=True),
        sa.Column("stt_best_text", sa.Text(), nullable=True),
        sa.Column("stt_raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("llm_response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("selected_text", sa.Text(), nullable=True),
        sa.Column("saved_vocab_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["saved_vocab_id"], ["vocab_items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lookup_events_user_id", "lookup_events", ["user_id"])

    op.create_table(
        "vocab_tags",
        sa.Column("vocab_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["vocab_id"], ["vocab_items.id"]),
        sa.PrimaryKeyConstraint("vocab_id", "tag"),
        sa.UniqueConstraint("vocab_id", "tag", name="uq_vocab_tag"),
    )

    op.create_table(
        "review_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vocab_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stability", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.Float(), nullable=False),
        sa.Column("due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.Column("last_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state", sa.SmallInteger(), nullable=False),
        sa.Column("suspended", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vocab_id"], ["vocab_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vocab_id"),
    )
    op.create_index("ix_review_cards_user_id", "review_cards", ["user_id"])
    op.create_index("ix_review_cards_due", "review_cards", ["user_id", "due"])

    op.create_table(
        "review_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("scheduled_due_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_due_after", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["card_id"], ["review_cards.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_logs_card_id", "review_logs", ["card_id"])


def downgrade() -> None:
    op.drop_index("ix_review_logs_card_id", table_name="review_logs")
    op.drop_table("review_logs")
    op.drop_index("ix_review_cards_due", table_name="review_cards")
    op.drop_index("ix_review_cards_user_id", table_name="review_cards")
    op.drop_table("review_cards")
    op.drop_table("vocab_tags")
    op.drop_index("ix_lookup_events_user_id", table_name="lookup_events")
    op.drop_table("lookup_events")
    op.drop_index("ix_vocab_items_user_id", table_name="vocab_items")
    op.drop_table("vocab_items")
    op.drop_index("ix_sources_user_id", table_name="sources")
    op.drop_table("sources")
    op.drop_table("users")
    sa.Enum(name="vocab_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="source_kind").drop(op.get_bind(), checkfirst=True)