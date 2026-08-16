"""Job source management + ingestion. Adapter dispatch/upsert logic here is
shared by the scheduler-triggered worker task (sync) and used to seed
default sources on first boot; simple CRUD/listing for the router lives
here too (async), so routers/jobs.py stays a thin HTTP layer.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.integrations.job_sources import NormalizedJobPosting, get_adapter
from app.models.job import JobPosting, JobSource

log = structlog.get_logger()

# Seeded once (migration/startup) as global sources (user_id=None) so a
# fresh install has real job flow without any manual configuration. Users
# can deactivate any of these, or add their own on top (including more
# Greenhouse/Lever boards or regional RSS feeds) from Settings.
DEFAULT_SOURCES: list[dict] = [
    {"type": "remotive", "name": "Remotive - Software Engineering", "config": {"query": "software engineer"}},
    {"type": "remoteok", "name": "RemoteOK - Dev", "config": {"query": "dev"}},
    {"type": "arbeitnow", "name": "Arbeitnow - Tech", "config": {"query": "developer"}},
    {"type": "themuse", "name": "The Muse - Engineering", "config": {"category": "Engineering"}},
]


def _content_hash(posting: NormalizedJobPosting) -> str:
    blob = "|".join(
        [
            posting.title,
            posting.company,
            posting.location,
            posting.description_text,
            str(posting.salary_min),
            str(posting.salary_max),
        ]
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def upsert_postings(db: Session, source: JobSource, postings: list[NormalizedJobPosting]) -> tuple[int, int]:
    """Returns (new_count, updated_count). Newly-created and changed rows
    are queued for embedding/matching by the caller (ingestion_tasks.py).
    """
    new_count = 0
    updated_count = 0
    changed_ids: list[UUID] = []

    for np in postings:
        if not np.external_id:
            continue
        content_hash = _content_hash(np)
        existing = db.execute(
            select(JobPosting).where(
                JobPosting.source_id == source.id, JobPosting.external_id == np.external_id
            )
        ).scalar_one_or_none()

        if existing is None:
            row = JobPosting(
                source_id=source.id,
                external_id=np.external_id,
                title=np.title,
                company=np.company,
                location=np.location,
                remote_type=np.remote_type,
                description_text=np.description_text,
                salary_min=np.salary_min,
                salary_max=np.salary_max,
                salary_currency=np.salary_currency,
                salary_period=np.salary_period,
                url=np.url,
                apply_url=np.apply_url,
                posted_at=np.posted_at,
                tags=np.tags,
                content_hash=content_hash,
                is_active=True,
            )
            db.add(row)
            db.flush()
            new_count += 1
            changed_ids.append(row.id)
        elif existing.content_hash != content_hash:
            existing.title = np.title
            existing.company = np.company
            existing.location = np.location
            existing.remote_type = np.remote_type
            existing.description_text = np.description_text
            existing.salary_min = np.salary_min
            existing.salary_max = np.salary_max
            existing.salary_currency = np.salary_currency
            existing.salary_period = np.salary_period
            existing.url = np.url
            existing.apply_url = np.apply_url
            existing.posted_at = np.posted_at
            existing.tags = np.tags
            existing.content_hash = content_hash
            existing.is_active = True
            updated_count += 1
            changed_ids.append(existing.id)

    db.commit()

    # Enqueue embedding regeneration for anything new/changed. Imported
    # locally to avoid a hard import cycle between services <-> workers.
    from app.workers.queue import llm_queue

    for job_id in changed_ids:
        llm_queue().enqueue("app.workers.embedding_tasks.generate_job_embedding", str(job_id))

    return new_count, updated_count


def poll_source_sync(db: Session, source: JobSource) -> None:
    """Fetches + upserts a single source. Never raises - failures are
    recorded on the source row so one bad source doesn't break the sweep.
    """
    import asyncio

    adapter = get_adapter(source.type)
    if adapter is None:
        source.last_poll_status = "error"
        source.last_poll_error = f"No adapter registered for type '{source.type}'"
        db.commit()
        return

    try:
        postings = asyncio.run(adapter.fetch(source.config or {}))
        new_count, updated_count = upsert_postings(db, source, postings)
        source.last_poll_status = "ok"
        source.last_poll_error = ""
        log.info(
            "ingestion.poll_ok",
            source=source.name,
            type=source.type,
            new=new_count,
            updated=updated_count,
            fetched=len(postings),
        )
    except Exception as exc:  # noqa: BLE001 - one source's failure must not break the sweep
        log.exception("ingestion.poll_failed", source=source.name, type=source.type)
        source.last_poll_status = "error"
        source.last_poll_error = str(exc)[:2000]

    source.last_polled_at = datetime.now(timezone.utc)
    db.commit()


# --- async CRUD/listing for the router ------------------------------------


async def list_sources(db: AsyncSession, user_id: UUID) -> list[JobSource]:
    stmt = select(JobSource).where(
        (JobSource.user_id == user_id) | (JobSource.user_id.is_(None))
    ).order_by(JobSource.created_at)
    return list((await db.execute(stmt)).scalars().all())


async def create_source(db: AsyncSession, user_id: UUID, data: dict) -> JobSource:
    source = JobSource(user_id=user_id, **data)
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_source(db: AsyncSession, user_id: UUID, source_id: UUID) -> bool:
    source = await db.get(JobSource, source_id)
    if source is None or source.user_id != user_id:
        return False
    await db.delete(source)
    await db.commit()
    return True


async def set_source_active(db: AsyncSession, user_id: UUID, source_id: UUID, is_active: bool) -> JobSource | None:
    source = await db.get(JobSource, source_id)
    if source is None:
        return None
    # Users may toggle default (global) sources off for themselves-in-effect
    # by deactivating them; only the creator can delete a custom one.
    if source.user_id is not None and source.user_id != user_id:
        return None
    source.is_active = is_active
    await db.commit()
    await db.refresh(source)
    return source


async def list_postings(
    db: AsyncSession,
    query: str | None = None,
    location: str | None = None,
    remote_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[JobPosting]:
    stmt = select(JobPosting).where(JobPosting.is_active.is_(True))
    if query:
        like = f"%{query}%"
        stmt = stmt.where(JobPosting.title.ilike(like) | JobPosting.company.ilike(like))
    if location:
        stmt = stmt.where(JobPosting.location.ilike(f"%{location}%"))
    if remote_type:
        stmt = stmt.where(JobPosting.remote_type == remote_type)
    stmt = stmt.order_by(JobPosting.posted_at.desc().nulls_last()).offset(offset).limit(limit)
    return list((await db.execute(stmt)).scalars().all())
