from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.surplus import SurplusLookupError, complete_lookup_json
from app.schemas import LookupLlmResult, LookupResponse, SttResult
from app.services.quick_translate import try_quick_translate
from app.services.stt_whisper import SttError, transcribe_audio_bytes
from app.services.users import ensure_default_user, ensure_language
from app.settings import get_settings


def _stt_only_llm(stt_text: str) -> LookupLlmResult:
    text = stt_text.strip()
    return LookupLlmResult(
        normalized_en=text,
        translation_es="",
        example_en="",
        example_es=None,
        alternatives=[],
        needs_user_pick=False,
    )


def _resolve_llm(stt_text: str, context_note: str | None) -> tuple[LookupLlmResult, bool, str | None, str]:
    """Devuelve (resultado, ok, error, translation_source)."""
    has_context = bool((context_note or "").strip())

    if not has_context:
        quick = try_quick_translate(stt_text)
        if quick:
            return quick, True, None, "dictionary"

    s = get_settings()
    if s.lookup_llm_enabled:
        try:
            llm = complete_lookup_json(stt_text=stt_text, context_note=context_note)
            return llm, True, None, "llm"
        except SurplusLookupError as exc:
            if not has_context:
                quick = try_quick_translate(stt_text)
                if quick:
                    return quick, True, f"LLM no disponible; diccionario: {exc}", "dictionary"
            return _stt_only_llm(stt_text), False, str(exc), "none"

    if has_context:
        return (
            _stt_only_llm(stt_text),
            False,
            "Hay nota de contexto: activa LOOKUP_LLM_ENABLED para traducir frases.",
            "none",
        )

    quick = try_quick_translate(stt_text)
    if quick:
        return quick, True, None, "dictionary"

    return (
        _stt_only_llm(stt_text),
        False,
        "No se pudo traducir (diccionario) y el fallback LLM está desactivado.",
        "none",
    )


def _build_response(
    *,
    language_code: str,
    stt: SttResult,
    llm: LookupLlmResult,
    llm_ok: bool,
    llm_error: str | None,
    stt_source: str,
    translation_source: str,
) -> LookupResponse:
    effective = (llm.normalized_en.strip() if llm_ok else "") or stt.best_text.strip()
    return LookupResponse(
        language_code=language_code.strip().lower(),
        stt=stt,
        llm=llm,
        effective_text=effective,
        llm_ok=llm_ok,
        llm_error=llm_error,
        stt_source=stt_source,
        translation_source=translation_source,
    )


async def run_lookup_from_text(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    language_code: str,
    text: str,
    context_note: str | None,
    stt_source: str = "browser",
) -> LookupResponse:
    await ensure_default_user(db, user_id)
    await ensure_language(db, language_code)

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Texto vacío")

    stt = SttResult(best_text=cleaned, segments=[], language=language_code)
    llm, llm_ok, llm_error, tr_src = _resolve_llm(cleaned, context_note)
    return _build_response(
        language_code=language_code,
        stt=stt,
        llm=llm,
        llm_ok=llm_ok,
        llm_error=llm_error,
        stt_source=stt_source,
        translation_source=tr_src,
    )


async def run_lookup(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    language_code: str,
    audio: bytes,
    content_type: str | None,
    context_note: str | None,
) -> LookupResponse:
    await ensure_default_user(db, user_id)
    await ensure_language(db, language_code)

    try:
        stt: SttResult = transcribe_audio_bytes(audio, content_type=content_type)
    except SttError as exc:
        raise ValueError(str(exc)) from exc

    llm, llm_ok, llm_error, tr_src = _resolve_llm(stt.best_text, context_note)
    return _build_response(
        language_code=language_code,
        stt=stt,
        llm=llm,
        llm_ok=llm_ok,
        llm_error=llm_error,
        stt_source="whisper",
        translation_source=tr_src,
    )


async def refine_lookup(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    language_code: str,
    selected_text: str,
) -> LookupResponse:
    await ensure_default_user(db, user_id)
    await ensure_language(db, language_code)

    stt = SttResult(best_text=selected_text.strip(), segments=[], language=language_code)
    llm, llm_ok, llm_error, tr_src = _resolve_llm(selected_text.strip(), None)
    return _build_response(
        language_code=language_code,
        stt=stt,
        llm=llm,
        llm_ok=llm_ok,
        llm_error=llm_error,
        stt_source="manual",
        translation_source=tr_src,
    )