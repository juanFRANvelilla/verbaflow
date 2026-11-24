import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """Sin contraseña en MVP; JWT más adelante (email como identidad futura)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Language(Base):
    """Idioma que estudias (de momento solo inglés)."""

    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class VocabularyEntry(Base):
    """Palabra o frase guardada, ligada a un idioma."""

    __tablename__ = "vocabulary_entries"
    __table_args__ = (UniqueConstraint("user_id", "language_code", "text", name="uq_vocab_user_lang_text"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    language_code: Mapped[str] = mapped_column(String(16), ForeignKey("languages.code"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    example_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())