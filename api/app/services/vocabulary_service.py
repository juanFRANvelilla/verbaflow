from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VocabularyEntry
from app.schemas import VocabularyEntryCreate
from app.services.users import ensure_default_user, ensure_language


async def create_entry(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    body: VocabularyEntryCreate,
) -> VocabularyEntry:
    await ensure_default_user(db, user_id)
    code = body.language_code.strip().lower()
    await ensure_language(db, code)

    text = body.text.strip()
    translation = body.translation.strip()

    existing = await db.scalar(
        select(VocabularyEntry).where(
            VocabularyEntry.user_id == user_id,
            VocabularyEntry.language_code == code,
            VocabularyEntry.text == text,
        )
    )
    if existing:
        existing.translation = translation
        existing.example_text = body.example_text.strip() if body.example_text else existing.example_text
        await db.commit()
        await db.refresh(existing)
        return existing

    entry = VocabularyEntry(
        user_id=user_id,
        language_code=code,
        text=text,
        translation=translation,
        example_text=body.example_text.strip() if body.example_text else None,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_entries(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    language_code: str | None,
    limit: int,
) -> list[VocabularyEntry]:
    stmt = (
        select(VocabularyEntry)
        .where(VocabularyEntry.user_id == user_id)
        .order_by(VocabularyEntry.created_at.desc())
        .limit(limit)
    )
    if language_code and language_code.strip():
        stmt = stmt.where(VocabularyEntry.language_code == language_code.strip().lower())
    return list((await db.scalars(stmt)).all())