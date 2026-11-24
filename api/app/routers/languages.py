from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import LanguageOut
from app.services.users import list_languages

router = APIRouter(prefix="/api/languages", tags=["languages"])


@router.get("", response_model=list[LanguageOut])
async def get_languages(db: AsyncSession = Depends(get_db)) -> list[LanguageOut]:
    rows = await list_languages(db)
    return [LanguageOut.model_validate(r) for r in rows]