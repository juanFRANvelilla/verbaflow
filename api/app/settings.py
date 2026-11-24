from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "verbaflow-api"
    debug: bool = False
    api_key: str = ""
    default_user_id: UUID = UUID("00000000-0000-4000-8000-000000000001")

    database_url: str = "postgresql+asyncpg://verbaflow:verbaflow@localhost:5432/verbaflow"

    surplusintelligence_api_key: str = ""
    surplus_base_url: str = "https://api.surplusintelligence.ai/v1"
    surplus_model_lookup: str = ""
    openai_timeout_seconds: float = 120.0

    whisper_model: str = "base.en"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_max_audio_seconds: int = 30

    lookup_llm_temperature: float = 0.25
    lookup_llm_max_tokens: int = 512


@lru_cache
def get_settings() -> Settings:
    return Settings()