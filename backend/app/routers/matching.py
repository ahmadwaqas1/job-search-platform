from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.match import MatchOut
from app.services import matching_service
from app.services.profile_service import get_or_create_profile
from app.workers.queue import llm_queue

router = APIRouter(prefix="/matches", tags=["matching"])


@router.get("", response_model=list[MatchOut])
async def list_matches(
    min_score: float | None = Query(None, ge=0, le=100),
    limit: int = Query(100, le=300),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = await get_or_create_profile(db, user)
    return await matching_service.list_matches(db, profile.id, limit=limit, min_score=min_score)


@router.get("/{job_posting_id}", response_model=MatchOut | None)
async def get_match(
    job_posting_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    profile = await get_or_create_profile(db, user)
    return await matching_service.get_match_for_job(db, profile.id, job_posting_id)


@router.post("/refresh", status_code=202)
async def refresh_my_matches(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """The one on-demand recompute path (e.g. right after editing your
    profile) - everything else is precomputed by background workers.
    """
    profile = await get_or_create_profile(db, user)
    llm_queue().enqueue("app.workers.embedding_tasks.generate_profile_embedding", str(profile.id))
    return {"status": "queued"}
