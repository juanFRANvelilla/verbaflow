from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Language, User


async def ensure_default_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    row = await db.get(User, user_id)
    if row is None:
        db.add(User(id=user_id, display_name="default"))
        await db.commit()


async def ensure_language(db: AsyncSession, code: str) -> Language:
    normalized = code.strip().lower()
    row = await db.get(Language, normalized)
    if row is None:
        raise ValueError(f"Idioma no configurado: {normalized}")
    if not row.enabled:
        raise ValueError(f"Idioma deshabilitado: {normalized}")
    return row


async def list_languages(db: AsyncSession) -> list[Language]:
    stmt = select(Language).where(Language.enabled.is_(True)).order_by(Language.name.asc())
    return list((await db.scalars(stmt)).all())


async def seed_bootstrap(db: AsyncSession) -> None:
    """Inserta inglés y usuario por defecto si no existen (idempotente)."""
    if await db.get(Language, "en") is None:
        db.add(Language(code="en", name="English", enabled=True))

    default_id = uuid.UUID("00000000-0000-4000-8000-000000000001")
    if await db.get(User, default_id) is None:
        db.add(User(id=default_id, display_name="default"))

    await db.commit()