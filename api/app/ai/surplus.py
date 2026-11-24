"""Cliente Surplus Intelligence (OpenAI-compatible) + satélite para elegir modelo."""
from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.ai.satellite_client import SatellitePickError, pick_surplus_model_for_lookup
from app.schemas import LookupLlmResult
from app.settings import get_settings

_SURPLUS_MAX_ATTEMPTS = 3


class SurplusLookupError(RuntimeError):
    pass


def _client(*, model: str) -> OpenAI:
    s = get_settings()
    key = (s.surplusintelligence_api_key or "").strip()
    if not key:
        raise SurplusLookupError("Falta SURPLUSINTELLIGENCE_API_KEY")
    if not (model or "").strip():
        raise SurplusLookupError("Falta modelo Surplus")
    return OpenAI(api_key=key, base_url=s.surplus_base_url.rstrip("/"), timeout=s.openai_timeout_seconds)


def _lookup_messages(stt_text: str, context_note: str | None) -> list[dict[str, Any]]:
    note = f"\nContexto del usuario: {context_note}" if context_note else ""
    system = (
        "Eres un asistente para hispanohablantes aprendiendo inglés. "
        "Recibes texto en inglés procedente de transcripción por voz (puede estar mal). "
        "Responde SOLO con JSON válido según el esquema pedido."
    )
    user = (
        f"Transcripción STT: {stt_text!r}.{note}\n"
        "Devuelve JSON con: normalized_en, translation_es, example_en, example_es, "
        "alternatives (lista de {{en, reason, confidence}}), "
        "needs_user_pick (true si hay ambigüedad fonética o la frase no tiene sentido)."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _resolve_lookup_model(exclude: set[str]) -> str:
    s = get_settings()
    if s.surplus_satellite_enabled:
        try:
            return pick_surplus_model_for_lookup(exclude_models=exclude)
        except SatellitePickError:
            pass
    fallback = (s.surplus_model_lookup or "").strip()
    if fallback and fallback not in exclude:
        return fallback
    raise SurplusLookupError(
        "No hay modelo Surplus: satélite falló y falta SURPLUS_MODEL_LOOKUP de respaldo"
    )


def _is_retriable_model_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in (
            "404",
            "discount",
            "marketplace",
            "notfound",
            "rate",
            "503",
            "abandoned",
        )
    )


def complete_lookup_json(*, stt_text: str, context_note: str | None = None) -> LookupLlmResult:
    s = get_settings()
    messages = _lookup_messages(stt_text, context_note)
    abandoned: set[str] = set()
    last_err = "sin respuesta"

    for _round in range(max(3, s.surplus_satellite_model_retries)):
        model = _resolve_lookup_model(abandoned)
        client = _client(model=model)

        for attempt in range(1, _SURPLUS_MAX_ATTEMPTS + 1):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=s.lookup_llm_temperature,
                    max_tokens=s.lookup_llm_max_tokens,
                )
                raw = resp.choices[0].message.content if resp.choices else None
                if not isinstance(raw, str) or not raw.strip():
                    last_err = "content vacío"
                    continue
                data = json.loads(raw)
                return LookupLlmResult.model_validate(data)
            except SurplusLookupError:
                raise
            except Exception as exc:
                last_err = f"{type(exc).__name__}: {exc}"
                if _is_retriable_model_error(exc):
                    abandoned.add(model)
                    break

    raise SurplusLookupError(f"Surplus agotó reintentos ({last_err})")