from pydantic import BaseModel


class EffectiveSettingsOut(BaseModel):
    ollama_base_url: str
    ollama_chat_model: str
    ollama_embed_model: str
    max_upload_mb: int
    default_job_poll_interval_minutes: int
    adzuna_configured: bool
    usajobs_configured: bool
    bls_configured: bool
