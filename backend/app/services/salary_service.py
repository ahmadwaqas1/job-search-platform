"""Salary/market insights. Three sources, in order of reliability for this
self-hosted app:

1. `aggregated_postings` - percentiles computed directly from salary fields
   on already-ingested job_postings. Always available, no API key needed,
   degrades gracefully to "no data" only when truly nothing's been
   ingested for that role/location yet.
2. `adzuna` - live estimate from Adzuna's search results, if configured.
3. `bls` - opt-in, only for roles the operator has mapped a verified BLS
   series ID for (see integrations/salary_apis/bls.py).

The nightly refresh (workers/salary_tasks.py) precomputes snapshots for a
curated list of common tech roles/locations; the read endpoint also
computes aggregated_postings live for arbitrary queries that aren't in the
curated list, so the Market page never just says "no data" for a
reasonable search.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.models.salary import SalarySnapshot

log = structlog.get_logger()

COMMON_ROLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Data Engineer",
    "DevOps Engineer",
    "Product Manager",
    "Engineering Manager",
    "QA Engineer",
    "UX Designer",
]
COMMON_LOCATIONS = ["Remote", "United States", "United Kingdom", "Canada", "Germany", "India"]

SNAPSHOT_FRESH_FOR = timedelta(hours=25)  # slightly over the daily cron cadence


def _postings_query(role_title: str, location: str | None):
    like = f"%{role_title}%"
    stmt = select(JobPosting.salary_min, JobPosting.salary_max).where(JobPosting.title.ilike(like))
    if location:
        stmt = stmt.where(JobPosting.location.ilike(f"%{location}%"))
    return stmt.where(JobPosting.salary_min.is_not(None) | JobPosting.salary_max.is_not(None))


def _percentiles_from_rows(rows) -> dict | None:
    values: list[float] = []
    for smin, smax in rows:
        if smin is not None and smax is not None:
            values.append((smin + smax) / 2)
        elif smin is not None:
            values.append(smin)
        elif smax is not None:
            values.append(smax)

    if len(values) < 3:
        return None

    values.sort()
    n = len(values)

    def pct(p: float) -> float:
        return values[min(n - 1, max(0, round(p * (n - 1))))]

    return {"p10": pct(0.10), "median": pct(0.50), "p90": pct(0.90), "sample_size": n}


# --- sync (cron task) -------------------------------------------------------


def compute_aggregated_sync(db: Session, role_title: str, location: str | None) -> dict | None:
    rows = db.execute(_postings_query(role_title, location)).all()
    return _percentiles_from_rows(rows)


def upsert_snapshot_sync(db: Session, role_title: str, location: str, source: str, data: dict) -> None:
    existing = db.execute(
        select(SalarySnapshot).where(
            SalarySnapshot.role_title == role_title,
            SalarySnapshot.location == location,
            SalarySnapshot.source == source,
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = SalarySnapshot(role_title=role_title, location=location, source=source)
        db.add(existing)

    existing.currency = data.get("currency") or "USD"
    existing.period = data.get("period", "year")
    existing.p10 = data.get("p10")
    existing.median = data.get("median")
    existing.p90 = data.get("p90")
    existing.sample_size = data.get("sample_size", 0)
    existing.fetched_at = datetime.now(timezone.utc)
    db.commit()


# --- async (read path) ------------------------------------------------------


async def compute_aggregated_async(db: AsyncSession, role_title: str, location: str | None) -> dict | None:
    rows = (await db.execute(_postings_query(role_title, location))).all()
    return _percentiles_from_rows(rows)


async def get_cached_snapshots(db: AsyncSession, role_title: str, location: str) -> list[SalarySnapshot]:
    stmt = select(SalarySnapshot).where(
        SalarySnapshot.role_title == role_title, SalarySnapshot.location == location
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_salary_insights(db: AsyncSession, role_title: str, location: str = "") -> list[SalarySnapshot]:
    """Returns whatever cached snapshots exist for this exact role/location,
    plus a freshly-computed aggregated_postings figure if nothing cached
    is fresh - so arbitrary searches outside the curated cron list still
    get a live answer instead of an empty page.
    """
    cached = await get_cached_snapshots(db, role_title, location)
    now = datetime.now(timezone.utc)
    has_fresh = any(
        s.source == "aggregated_postings" and s.fetched_at and (now - s.fetched_at) < SNAPSHOT_FRESH_FOR
        for s in cached
    )
    if not has_fresh:
        live = await compute_aggregated_async(db, role_title, location or None)
        if live is not None:
            cached = [
                s for s in cached if s.source != "aggregated_postings"
            ] + [
                SalarySnapshot(
                    role_title=role_title,
                    location=location,
                    source="aggregated_postings",
                    currency="USD",
                    period="year",
                    p10=live["p10"],
                    median=live["median"],
                    p90=live["p90"],
                    sample_size=live["sample_size"],
                    fetched_at=now,
                )
            ]
    return cached
