"""Central application settings, loaded from environment variables / .env.

Every other module reads configuration through `get_settings()` rather than
`os.environ` directly, so tests can override settings by constructing a
`Settings(...)` instance instead of mutating the environment.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- core / security ---
    secret_key: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 10080
    jwt_algorithm: str = "HS256"
    allow_registration_if_empty: bool = True

    # --- database ---
    database_url: str = "postgresql+asyncpg://jobsearch:jobsearch@localhost:5432/jobsearch"
    sync_database_url: str = "postgresql+psycopg://jobsearch:jobsearch@localhost:5432/jobsearch"

    # --- redis / queues ---
    redis_url: str = "redis://localhost:6379/0"

    # --- ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_embed_dim: int = 768
    ollama_request_timeout_seconds: int = 120

    # --- uploads ---
    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 10

    # --- job source API keys (optional) ---
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "us"
    usajobs_api_key: str = ""
    usajobs_user_agent: str = ""
    bls_api_key: str = ""

    # --- scheduling ---
    scheduler_sweep_interval_minutes: int = 5
    default_job_poll_interval_minutes: int = 60
    salary_refresh_cron_hour: int = 3

    # --- cors (dev convenience; the shipped nginx frontend is same-origin) ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
