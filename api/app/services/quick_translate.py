"""Traducción rápida sin LLM: deep-translator + ejemplos Free Dictionary API."""
from __future__ import annotations

import re
from urllib.parse import quote

import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator

from app.schemas import LookupLlmResult
from app.settings import get_settings


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _google_dict_translate(text: str) -> str | None:
    """Traducción liviana estilo diccionario (sin API key)."""
    try:
        resp = requests.get(
            "https://clients5.google.com/translate_a/t",
            params={"client": "dict-chrome-ex", "sl": "en", "tl": "es", "q": text},
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Verbaflow/1.0)"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if isinstance(data, list) and data:
            if isinstance(data[0], str):
                return data[0].strip()
            if isinstance(data[0], list) and data[0]:
                first = data[0][0]
                return str(first).strip() if first else None
    except (requests.RequestException, ValueError, TypeError):
        return None
    return None


def _dictionary_example(word: str) -> tuple[str, str | None]:
    """Primera definición + ejemplo en inglés (si existe)."""
    w = word.strip().lower()
    if not w or " " in w:
        return "", None
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(w)}",
            timeout=6,
        )
        if resp.status_code != 200:
            return "", None
        entries = resp.json()
        if not isinstance(entries, list) or not entries:
            return "", None
        meanings = entries[0].get("meanings") if isinstance(entries[0], dict) else None
        if not meanings:
            return "", None
        for meaning in meanings:
            defs = meaning.get("definitions") or []
            for d in defs:
                ex = (d.get("example") or "").strip() if isinstance(d, dict) else ""
                if ex:
                    return ex, None
    except requests.RequestException:
        return "", None
    return "", None


def try_quick_translate(text: str) -> LookupLlmResult | None:
    s = get_settings()
    if not s.lookup_quick_translate_enabled:
        return None

    cleaned = _normalize(text)
    if not cleaned:
        return None

    words = cleaned.split()
    if len(words) > s.lookup_dictionary_max_words:
        return None

    translation = _google_dict_translate(cleaned)
    if not translation:
        for attempt in (
            lambda: MyMemoryTranslator(source="en-GB", target="es-ES").translate(cleaned),
            lambda: GoogleTranslator(source="en", target="es").translate(cleaned),
        ):
            try:
                translation = attempt()
                break
            except Exception:
                continue
    if translation is None:
        return None

    if not translation or not translation.strip():
        return None

    tr = translation.strip()
    if tr.lower() == cleaned.lower():
        return None

    example_en, example_es = _dictionary_example(cleaned) if len(words) == 1 else ("", None)
    if not example_en and len(words) <= 3:
        example_en = f"... {cleaned} ..."

    return LookupLlmResult(
        normalized_en=cleaned,
        translation_es=tr,
        example_en=example_en or "",
        example_es=example_es,
        alternatives=[],
        needs_user_pick=False,
    )