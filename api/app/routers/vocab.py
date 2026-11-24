from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import current_user_id
from app.models import VocabItem
from app.schemas import VocabItemOut

router = APIRouter(prefix="/api/vocab", tags=["vocab"])


@router.get("", response_model=list[VocabItemOut])
async def list_vocab(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> list[VocabItemOut]:
    stmt = select(VocabItem).where(VocabItem.user_id == user_id).order_by(VocabItem.created_at.desc()).limit(limit)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(VocabItem.canonical_en.ilike(like))
    rows = (await db.scalars(stmt)).all()
    return [VocabItemOut.model_validate(r) for r in rows]