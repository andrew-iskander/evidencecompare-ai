from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "EvidenceCompare AI"
    env: str = "dev"
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///./evidencecompare.db"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # CORS (accept a comma-separated string from env; NoDecode disables JSON parsing)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Pipeline
    pipeline_mode: str = "background"  # background | eager | celery
    pipeline_step_delay: float = 0.5

    # Report caching + living evidence.
    # Reuse a complete report for the same query within this window (hours).
    report_cache_ttl_hours: int = 168
    # Periodic living-evidence sweep re-checks complete reports older than this (hours).
    freshness_stale_hours: int = 168

    # Evidence engine (Phase 3)
    evidence_mode: str = "auto"  # auto | live | offline
    llm_mode: str = "auto"  # auto | live | offline
    http_timeout: float = 20.0
    ncbi_email: str = "evidencecompare@example.com"
    ncbi_api_key: str = ""
    max_docs_per_source: int = 12
    top_k_citations: int = 12
    embedding_dim: int = 256  # offline pseudo-embedding dimension

    # AI providers (used from Phase 3)
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    model_synthesis: str = "claude-opus-4-8"
    model_agent: str = "claude-sonnet-5"
    model_extract: str = "claude-haiku-4-5"
    embedding_model: str = "voyage-3.5"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
