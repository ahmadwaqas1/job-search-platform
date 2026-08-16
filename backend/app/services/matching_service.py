"""Smart Match pipeline.

Three stages, deliberately kept cheap-then-expensive so the LLM is never
called synchronously on a page load:

1. Embedding (workers/embedding_tasks.py) - profile/job text -> vector,
   stored on the row itself.
2. Candidate search (this module, `find_candidate_*`) - a pure pgvector
   cosine-distance query, cheap enough to run on every embedding change.
3. LLM explanation (this module, `explain_match`) - only for candidates
   above SIMILARITY_FLOOR, and only via a background task.

The read path (routers/matching.py) only ever selects from the precomputed
`matches` table.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.integrations.ollama_client import OllamaClient
from app.models.job import JobPosting
from app.models.match import Match
from app.models.profile import Profile

log = structlog.get_logger()

CANDIDATE_LIMIT = 50
SIMILARITY_FLOOR = 0.5  # cosine similarity; below this we don't bother with an LLM pass

MATCH_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "description": "Overall fit score, 0-100"},
        "explanation": {"type": "string", "description": "2-4 sentences on why this job fits (or doesn't)"},
        "matched_skills": {"type": "array", "items": {"type": "string"}},
        "missing_skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["score", "explanation", "matched_skills", "missing_skills"],
}

MATCH_SYSTEM_PROMPT = (
    "You are a career-matching assistant. Given a candidate profile summary and a job "
    "posting, judge how well the candidate fits the role. Be honest and specific - call "
    "out real gaps, don't just flatter. Respond with ONLY JSON matching the given schema."
)


# --- stage 2: candidate search (sync, called from RQ tasks) ---------------


def find_candidate_jobs_for_profile(
    db: Session, profile: Profile, limit: int = CANDIDATE_LIMIT
) -> list[tuple[JobPosting, float]]:
    if profile.embedding is None:
        return []
    distance = JobPosting.embedding.cosine_distance(profile.embedding)
    stmt = (
        select(JobPosting, (1 - distance).label("similarity"))
        .where(JobPosting.embedding.is_not(None))
        .where(JobPosting.is_active.is_(True))
        .order_by(distance)
        .limit(limit)
    )
    return [(row[0], float(row[1])) for row in db.execute(stmt).all()]


def find_candidate_profiles_for_job(
    db: Session, posting: JobPosting, limit: int = CANDIDATE_LIMIT
) -> list[tuple[Profile, float]]:
    if posting.embedding is None:
        return []
    distance = Profile.embedding.cosine_distance(posting.embedding)
    stmt = (
        select(Profile, (1 - distance).label("similarity"))
        .where(Profile.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    return [(row[0], float(row[1])) for row in db.execute(stmt).all()]


def upsert_match_similarity(db: Session, profile_id: UUID, job_posting_id: UUID, similarity: float) -> Match:
    match = db.execute(
        select(Match).where(Match.profile_id == profile_id, Match.job_posting_id == job_posting_id)
    ).scalar_one_or_none()
    if match is None:
        match = Match(profile_id=profile_id, job_posting_id=job_posting_id)
        db.add(match)
    match.similarity_score = similarity
    db.flush()
    return match


# --- stage 3: LLM explanation (async call, wrapped for sync callers) ------


async def _explain_match_async(profile: Profile, posting: JobPosting) -> dict:
    client = OllamaClient()
    user_prompt = (
        f"CANDIDATE PROFILE:\n{profile.searchable_text()[:4000]}\n\n"
        f"JOB POSTING:\n{posting.searchable_text()[:4000]}\n\n"
        f"Vector similarity score (0-1, informational only): {SIMILARITY_FLOOR}"
    )
    return await client.generate_json(MATCH_SYSTEM_PROMPT, user_prompt, MATCH_JSON_SCHEMA)


def explain_match(db: Session, match: Match, profile: Profile, posting: JobPosting) -> None:
    """Runs the LLM explanation pass for a single match and writes the
    result. Caller (a worker task) is responsible for filtering to matches
    above SIMILARITY_FLOOR before calling this - it's the expensive step.
    """
    import asyncio

    try:
        result = asyncio.run(_explain_match_async(profile, posting))
        match.llm_score = float(result.get("score", 0))
        match.explanation_text = str(result.get("explanation", ""))
        match.matched_skills = list(result.get("matched_skills", []))
        match.missing_skills = list(result.get("missing_skills", []))
        match.computed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        log.exception("matching.explain_failed", match_id=str(match.id))
        db.rollback()


# --- read path (async, used by routers/matching.py) -----------------------


async def list_matches(
    db: AsyncSession, profile_id: UUID, limit: int = 100, min_score: float | None = None
) -> list[Match]:
    from sqlalchemy.orm import selectinload

    stmt = (
        select(Match)
        .where(Match.profile_id == profile_id)
        .options(selectinload(Match.job_posting))
        .order_by(Match.llm_score.desc().nulls_last(), Match.similarity_score.desc())
        .limit(limit)
    )
    if min_score is not None:
        stmt = stmt.where(Match.llm_score >= min_score)
    return list((await db.execute(stmt)).scalars().all())


async def get_match_for_job(db: AsyncSession, profile_id: UUID, job_posting_id: UUID) -> Match | None:
    stmt = select(Match).where(Match.profile_id == profile_id, Match.job_posting_id == job_posting_id)
    return (await db.execute(stmt)).scalar_one_or_none()
