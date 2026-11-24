from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import current_user_id
from app.schemas import VocabularyEntryCreate, VocabularyEntryOut
from app.services.vocabulary_service import create_entry, list_entries

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.post("", response_model=VocabularyEntryOut)
async def save_entry(
    body: VocabularyEntryCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> VocabularyEntryOut:
    entry = await create_entry(db, user_id=user_id, body=body)
    return VocabularyEntryOut.model_validate(entry)


@router.get("", response_model=list[VocabularyEntryOut])
async def get_entries(
    language_code: str | None = Query(default=None, max_length=16),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> list[VocabularyEntryOut]:
    rows = await list_entries(db, user_id=user_id, language_code=language_code, limit=limit)
    return [VocabularyEntryOut.model_validate(r) for r in rows]