"""Read-only view of the server's effective configuration, so the frontend
Settings page can show what's active (e.g. "Adzuna: configured") without
exposing secret values. Model/API-key configuration itself is done via the
server's .env file (see README) - job SOURCES (as opposed to server
config) are fully editable at runtime via /jobs/sources.
"""
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.deps import get_current_user
from app.models.user import User
from app.schemas.settings import EffectiveSettingsOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=EffectiveSettingsOut)
async def get_effective_settings(_user: User = Depends(get_current_user)):
    settings = get_settings()
    return EffectiveSettingsOut(
        ollama_base_url=settings.ollama_base_url,
        ollama_chat_model=settings.ollama_chat_model,
        ollama_embed_model=settings.ollama_embed_model,
        max_upload_mb=settings.max_upload_mb,
        default_job_poll_interval_minutes=settings.default_job_poll_interval_minutes,
        adzuna_configured=bool(settings.adzuna_app_id and settings.adzuna_app_key),
        usajobs_configured=bool(settings.usajobs_api_key),
        bls_configured=bool(settings.bls_api_key),
    )
