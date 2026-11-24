"""Transcripción con faster-whisper (carga perezosa del modelo)."""
from __future__ import annotations

import tempfile
from functools import lru_cache
from typing import TYPE_CHECKING

from app.schemas import SttResult
from app.settings import get_settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel


class SttError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SttError("faster-whisper no está instalado") from exc

    s = get_settings()
    return WhisperModel(s.whisper_model, device=s.whisper_device, compute_type=s.whisper_compute_type)


def transcribe_audio_bytes(data: bytes, *, content_type: str | None = None) -> SttResult:
    if not data:
        raise SttError("Audio vacío")

    s = get_settings()
    suffix = ".webm"
    if content_type and "ogg" in content_type:
        suffix = ".ogg"
    elif content_type and "wav" in content_type:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        segments, info = _model().transcribe(
            tmp.name,
            language="en",
            vad_filter=True,
            word_timestamps=False,
        )
        seg_list = []
        texts: list[str] = []
        for seg in segments:
            seg_list.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
            if seg.text.strip():
                texts.append(seg.text.strip())

    best = " ".join(texts).strip()
    if not best:
        raise SttError("No se detectó voz en inglés")
    return SttResult(best_text=best, segments=seg_list, language=getattr(info, "language", "en") or "en")