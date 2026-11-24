from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import current_user_id
from app.schemas import LookupRefineBody, LookupResponse, LookupTextBody
from app.services.lookup_service import refine_lookup, run_lookup, run_lookup_from_text

router = APIRouter(prefix="/api/lookup", tags=["lookup"])


@router.post("", response_model=LookupResponse)
async def create_lookup(
    audio: UploadFile = File(...),
    language_code: str = Form(default="en"),
    context_note: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> LookupResponse:
    data = await audio.read()
    try:
        return await run_lookup(
            db,
            user_id=user_id,
            language_code=language_code,
            audio=data,
            content_type=audio.content_type,
            context_note=context_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/text", response_model=LookupResponse)
async def create_lookup_from_text(
    body: LookupTextBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> LookupResponse:
    try:
        return await run_lookup_from_text(
            db,
            user_id=user_id,
            language_code=body.language_code,
            text=body.text,
            context_note=body.context_note,
            stt_source=body.stt_source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/refine", response_model=LookupResponse)
async def refine_alternative(
    body: LookupRefineBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> LookupResponse:
    try:
        return await refine_lookup(
            db,
            user_id=user_id,
            language_code=body.language_code,
            selected_text=body.selected_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc