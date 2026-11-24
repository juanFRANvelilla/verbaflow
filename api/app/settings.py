from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url


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

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/verbaflow"
    database_host: str | None = None
    cors_origins: str = "http://localhost:4200"

    surplusintelligence_api_key: str = ""
    surplus_base_url: str = "https://api.surplusintelligence.ai/v1"
    surplus_model_lookup: str = ""
    openai_timeout_seconds: float = 120.0

    surplus_database_url: str = ""
    surplus_satellite_enabled: bool = True
    surplus_satellite_base_url: str = "https://surplus-satellite.juanfranciscoperez.es"
    surplus_satellite_min_discount_pct: float = 80.0
    surplus_satellite_max_output_price_per_1m_usd: float = 0.35
    surplus_satellite_verify_model: bool = False
    surplus_satellite_pick_timeout_seconds: float = 30.0
    surplus_satellite_pick_retry_seconds: float = 2.0
    surplus_satellite_pick_max_attempts: int = 4
    surplus_satellite_model_retries: int = 5

    whisper_model: str = "base.en"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_max_audio_seconds: int = 30

    lookup_llm_temperature: float = 0.25
    lookup_llm_max_tokens: int = 512
    lookup_quick_translate_enabled: bool = True
    lookup_dictionary_max_words: int = 6
    lookup_llm_enabled: bool = True


    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        url = make_url(self.database_url)
        if self.database_host:
            url = url.set(host=self.database_host)
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()