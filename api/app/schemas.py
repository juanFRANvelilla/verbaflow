from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import SourceKind, VocabKind


class AlternativeCandidate(BaseModel):
    en: str
    reason: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class LookupLlmResult(BaseModel):
    normalized_en: str
    kind: VocabKind
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
    lookup_id: UUID
    stt: SttResult
    llm: LookupLlmResult
    effective_en: str


class LookupSelectBody(BaseModel):
    selected_text: str = Field(min_length=1)


class SaveLookupBody(BaseModel):
    source_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)


class VocabItemOut(BaseModel):
    id: UUID
    canonical_en: str
    kind: VocabKind
    translation_es: str
    example_en: str | None
    example_es: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewRating(int, Enum):
    again = 1
    hard = 2
    good = 3
    easy = 4


class ReviewCardOut(BaseModel):
    card_id: UUID
    vocab_id: UUID
    canonical_en: str
    translation_es: str | None = None
    example_en: str | None = None
    due: datetime

    model_config = {"from_attributes": True}


class ReviewAnswerBody(BaseModel):
    rating: ReviewRating


class SourceCreate(BaseModel):
    kind: SourceKind
    name: str = Field(min_length=1, max_length=500)