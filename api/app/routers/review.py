from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.deps import current_user_id
from app.models import ReviewCard, ReviewLog, VocabItem
from app.schemas import ReviewAnswerBody, ReviewCardOut
from app.services import fsrs_scheduler

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/due", response_model=list[ReviewCardOut])
async def due_cards(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> list[ReviewCardOut]:
    now = datetime.now(timezone.utc)
    stmt = (
        select(ReviewCard)
        .where(
            ReviewCard.user_id == user_id,
            ReviewCard.suspended.is_(False),
            ReviewCard.due <= now,
        )
        .order_by(ReviewCard.due.asc())
        .limit(limit)
    )
    cards = (await db.scalars(stmt)).all()
    out: list[ReviewCardOut] = []
    for card in cards:
        vocab = await db.get(VocabItem, card.vocab_id)
        if not vocab:
            continue
        out.append(
            ReviewCardOut(
                card_id=card.id,
                vocab_id=vocab.id,
                canonical_en=vocab.canonical_en,
                translation_es=None,
                example_en=vocab.example_en,
                due=card.due,
            )
        )
    return out


@router.post("/{card_id}/answer", response_model=ReviewCardOut)
async def answer_card(
    card_id: UUID,
    body: ReviewAnswerBody,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(current_user_id),
) -> ReviewCardOut:
    card = await db.get(ReviewCard, card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")

    vocab = await db.get(VocabItem, card.vocab_id)
    if not vocab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocab asociado no encontrado")

    due_before = card.due
    rating = fsrs_scheduler.rating_from_int(int(body.rating))
    stability, difficulty, due, reps, lapses, state, last_review = fsrs_scheduler.review_card_state(
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        reps=card.reps,
        lapses=card.lapses,
        state=card.state,
        rating=rating,
    )
    card.stability = stability
    card.difficulty = difficulty
    card.due = due
    card.reps = reps
    card.lapses = lapses
    card.state = state
    card.last_review = last_review

    db.add(
        ReviewLog(
            card_id=card.id,
            rating=int(body.rating),
            scheduled_due_before=due_before,
            scheduled_due_after=due,
        )
    )
    await db.commit()

    return ReviewCardOut(
        card_id=card.id,
        vocab_id=vocab.id,
        canonical_en=vocab.canonical_en,
        translation_es=vocab.translation_es,
        example_en=vocab.example_en,
        due=card.due,
    )