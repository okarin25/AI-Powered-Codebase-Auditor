"""Centralized application settings.

Loaded once via get_settings() (cached). Instantiating Settings() will raise
a validation error immediately if a required variable (GOOGLE_API_KEY) is
missing — this is intentional "fail fast" behavior so a misconfigured
deployment errors on startup instead of on the first real user request.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required
    google_api_key: str

    # Security
    api_key: str | None = None  # if set, all /api/* routes require X-API-Key header
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Repo / analysis limits
    max_repo_size_mb: float = 50
    max_files_to_analyze: int = 25
    clone_timeout_seconds: int = 60
    subprocess_timeout_seconds: int = 30

    # Job lifecycle
    job_ttl_hours: int = 6
    max_concurrent_jobs: int = 3

    # Gemini call resilience — confirmed live limit for gemini-2.5-flash-lite
    # is 10 RPM (check yours at https://aistudio.google.com/rate-limit).
    # Note: RPD (requests/day) is the real constraint on the free tier —
    # often as low as 20/day — meaning only a couple of full audits per day
    # are possible regardless of this RPM setting.
    gemini_requests_per_minute: int = 10
    agent_max_iterations: int = 8

    # Rate limiting
    rate_limit_audit: str = "5/minute"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # Pylance/mypy will flag the call below as "missing argument" because it
    # can't see that pydantic-settings populates required fields from
    # environment variables / .env at runtime. This is expected and safe.
    return Settings()  # type: ignore[call-arg]