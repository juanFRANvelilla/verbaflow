from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlternativeCandidate(BaseModel):
    en: str
    reason: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class LookupLlmResult(BaseModel):
    normalized_en: str
    translation_es: str
    example_en: str = ""
    example_es: str | None = None
    alternatives: list[AlternativeCandidate] = Field(default_factory=list)
    needs_user_pick: bool = False


class SttResult(BaseModel):
    best_text: str
    segments: list[dict] = Field(default_factory=list)
    language: str = "en"


class LookupResponse(BaseModel):
    language_code: str
    stt: SttResult
    llm: LookupLlmResult
    effective_text: str
    llm_ok: bool = True
    llm_error: str | None = None
    stt_source: str = "whisper"
    translation_source: str = Field(
        default="none",
        description="dictionary | llm | none",
    )


class LookupTextBody(BaseModel):
    language_code: str = Field(min_length=2, max_length=16)
    text: str = Field(min_length=1)
    context_note: str | None = None
    stt_source: str = Field(default="text", max_length=32)


class LookupRefineBody(BaseModel):
    language_code: str = Field(min_length=2, max_length=16)
    selected_text: str = Field(min_length=1)


class VocabularyEntryCreate(BaseModel):
    language_code: str = Field(min_length=2, max_length=16)
    text: str = Field(min_length=1)
    translation: str = Field(min_length=1)
    example_text: str | None = None


class VocabularyEntryOut(BaseModel):
    id: UUID
    language_code: str
    text: str
    translation: str
    example_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LanguageOut(BaseModel):
    code: str
    name: str
    enabled: bool

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}