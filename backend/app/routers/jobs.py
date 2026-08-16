from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.job import JOB_SOURCE_TYPES, JobPosting
from app.models.user import User
from app.schemas.job import JobPostingOut, JobSourceIn, JobSourceOut
from app.services import job_ingestion_service
from app.workers.queue import default_queue

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobPostingOut])
async def list_jobs(
    q: str | None = Query(None, description="Free-text search over title/company"),
    location: str | None = None,
    remote_type: str | None = Query(None, pattern="^(remote|hybrid|onsite|unknown)$"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await job_ingestion_service.list_postings(
        db, query=q, location=location, remote_type=remote_type, limit=limit, offset=offset
    )


@router.get("/{job_id}", response_model=JobPostingOut)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    posting = await db.get(JobPosting, job_id)
    if posting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job posting not found.")
    return posting


@router.get("/sources/list", response_model=list[JobSourceOut])
async def list_sources(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await job_ingestion_service.list_sources(db, user.id)


@router.post("/sources", response_model=JobSourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: JobSourceIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if payload.type not in JOB_SOURCE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"type must be one of {JOB_SOURCE_TYPES}")
    source = await job_ingestion_service.create_source(db, user.id, payload.model_dump())
    return source


@router.patch("/sources/{source_id}/active", response_model=JobSourceOut)
async def set_source_active(
    source_id: UUID,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    source = await job_ingestion_service.set_source_active(db, user.id, source_id, is_active)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job source not found.")
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    ok = await job_ingestion_service.delete_source(db, user.id, source_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job source not found or not deletable by you.")


@router.post("/sources/{source_id}/poll-now", status_code=status.HTTP_202_ACCEPTED)
async def poll_source_now(
    source_id: UUID, _db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)
):
    default_queue().enqueue("app.workers.ingestion_tasks.poll_source", str(source_id))
    return {"status": "queued"}
