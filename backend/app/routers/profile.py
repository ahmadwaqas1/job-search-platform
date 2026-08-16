from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut
from app.services import profile_service
from app.workers.queue import llm_queue

router = APIRouter(prefix="/profile", tags=["profile"])


def _to_out(profile) -> ProfileOut:
    out = ProfileOut.model_validate(profile)
    return out.model_copy(update={"has_embedding": profile.embedding is not None})


@router.get("", response_model=ProfileOut)
async def get_profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    profile = await profile_service.get_or_create_profile(db, user)
    return _to_out(profile)


@router.put("", response_model=ProfileOut)
async def update_profile(
    payload: ProfileIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    profile = await profile_service.replace_profile(db, user, payload)
    # Recompute embedding + matches in the background - never block the save.
    llm_queue().enqueue("app.workers.embedding_tasks.generate_profile_embedding", str(profile.id))
    return _to_out(profile)
