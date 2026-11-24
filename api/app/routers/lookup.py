from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import current_user_id
from app.schemas import LookupResponse, LookupSelectBody, SaveLookupBody, VocabItemOut
from app.services.lookup_service import LookupError, reselect_lookup, run_lookup, save_lookup

router = APIRouter(prefix="/api/lookup", tags=["lookup"])


@router.post("", response_model=LookupResponse)
async def create_lookup(
    audio: UploadFile = File(...),
    context_note: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> LookupResponse:
    data = await audio.read()
    try:
        return await run_lookup(
            db,
            user_id=user_id,
            audio=data,
            content_type=audio.content_type,
            context_note=context_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.patch("/{lookup_id}/select", response_model=LookupResponse)
async def select_alternative(
    lookup_id: UUID,
    body: LookupSelectBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> LookupResponse:
    try:
        return await reselect_lookup(db, user_id=user_id, lookup_id=lookup_id, selected_text=body.selected_text)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{lookup_id}/save", response_model=VocabItemOut)
async def save_from_lookup(
    lookup_id: UUID,
    body: SaveLookupBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> VocabItemOut:
    try:
        vocab = await save_lookup(
            db,
            user_id=user_id,
            lookup_id=lookup_id,
            source_id=body.source_id,
            tags=body.tags,
        )
        return VocabItemOut.model_validate(vocab)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc