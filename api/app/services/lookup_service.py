from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.surplus import SurplusLookupError, complete_lookup_json
from app.models import LookupEvent, ReviewCard, User, VocabItem, VocabKind, VocabTag
from app.schemas import LookupLlmResult, LookupResponse, SttResult
from app.services import fsrs_scheduler
from app.services.stt_whisper import SttError, transcribe_audio_bytes
from app.settings import get_settings


async def ensure_default_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    row = await db.get(User, user_id)
    if row is None:
        db.add(User(id=user_id, display_name="default"))
        await db.commit()


async def run_lookup(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    audio: bytes,
    content_type: str | None,
    context_note: str | None,
) -> LookupResponse:
    await ensure_default_user(db, user_id)
    s = get_settings()

    try:
        stt: SttResult = transcribe_audio_bytes(audio, content_type=content_type)
    except SttError as exc:
        raise ValueError(str(exc)) from exc

    try:
        llm: LookupLlmResult = complete_lookup_json(stt_text=stt.best_text, context_note=context_note)
    except SurplusLookupError as exc:
        raise ValueError(str(exc)) from exc

    effective = llm.normalized_en.strip() or stt.best_text.strip()
    event = LookupEvent(
        user_id=user_id,
        stt_model=s.whisper_model,
        llm_model=s.surplus_model_lookup,
        stt_best_text=stt.best_text,
        stt_raw_json={"segments": stt.segments, "language": stt.language},
        llm_response_json=llm.model_dump(mode="json"),
        selected_text=effective,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return LookupResponse(lookup_id=event.id, stt=stt, llm=llm, effective_en=effective)


async def reselect_lookup(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    lookup_id: uuid.UUID,
    selected_text: str,
) -> LookupResponse:
    event = await db.get(LookupEvent, lookup_id)
    if not event or event.user_id != user_id:
        raise LookupError("Lookup no encontrado")

    try:
        llm = complete_lookup_json(stt_text=selected_text.strip())
    except SurplusLookupError as exc:
        raise ValueError(str(exc)) from exc

    event.selected_text = selected_text.strip()
    event.llm_response_json = llm.model_dump(mode="json")
    await db.commit()

    stt = SttResult(best_text=selected_text.strip(), segments=[], language="en")
    effective = llm.normalized_en.strip() or selected_text.strip()
    return LookupResponse(lookup_id=event.id, stt=stt, llm=llm, effective_en=effective)


class LookupError(ValueError):
    pass


async def save_lookup(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    lookup_id: uuid.UUID,
    source_id: uuid.UUID | None,
    tags: list[str],
) -> VocabItem:
    event = await db.get(LookupEvent, lookup_id)
    if not event or event.user_id != user_id:
        raise LookupError("Lookup no encontrado")
    if not event.llm_response_json:
        raise LookupError("Lookup sin resultado LLM")

    llm = LookupLlmResult.model_validate(event.llm_response_json)
    canonical = (event.selected_text or llm.normalized_en).strip()

    existing = await db.scalar(
        select(VocabItem).where(VocabItem.user_id == user_id, VocabItem.canonical_en == canonical)
    )
    if existing:
        vocab = existing
        vocab.translation_es = llm.translation_es
        vocab.example_en = llm.example_en or vocab.example_en
        vocab.example_es = llm.example_es or vocab.example_es
        vocab.kind = llm.kind
        vocab.updated_at = datetime.now(timezone.utc)
    else:
        vocab = VocabItem(
            user_id=user_id,
            canonical_en=canonical,
            kind=llm.kind,
            translation_es=llm.translation_es,
            example_en=llm.example_en or None,
            example_es=llm.example_es,
            from_lookup_id=event.id,
            source_id=source_id,
        )
        db.add(vocab)
        await db.flush()

        stability, difficulty, due, reps, lapses, state = fsrs_scheduler.new_card_now()
        db.add(
            ReviewCard(
                vocab_id=vocab.id,
                user_id=user_id,
                stability=stability,
                difficulty=difficulty,
                due=due,
                reps=reps,
                lapses=lapses,
                state=state,
            )
        )

    for tag in {t.strip().lower() for t in tags if t.strip()}:
        db.add(VocabTag(vocab_id=vocab.id, tag=tag[:64]))

    event.saved_vocab_id = vocab.id
    await db.commit()
    await db.refresh(vocab)
    return vocab