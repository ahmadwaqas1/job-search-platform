"""RQ tasks that run the candidate-search + LLM-explain matching pipeline.
Triggered whenever a profile or job posting embedding is (re)generated -
see app/workers/embedding_tasks.py.
"""
from uuid import UUID

import structlog

from app.database import get_sync_session
from app.models.job import JobPosting
from app.models.profile import Profile
from app.services.matching_service import (
    SIMILARITY_FLOOR,
    explain_match,
    find_candidate_jobs_for_profile,
    find_candidate_profiles_for_job,
    upsert_match_similarity,
)

log = structlog.get_logger()


def find_and_score_matches_for_profile(profile_id: str) -> None:
    with get_sync_session() as db:
        profile = db.get(Profile, UUID(profile_id))
        if profile is None or profile.embedding is None:
            return

        candidates = find_candidate_jobs_for_profile(db, profile)
        log.info("matching.candidates_found", profile_id=profile_id, count=len(candidates))

        for posting, similarity in candidates:
            match = upsert_match_similarity(db, profile.id, posting.id, similarity)
            if similarity >= SIMILARITY_FLOOR:
                explain_match(db, match, profile, posting)
        db.commit()


def find_and_score_matches_for_job(job_posting_id: str) -> None:
    with get_sync_session() as db:
        posting = db.get(JobPosting, UUID(job_posting_id))
        if posting is None or posting.embedding is None:
            return

        candidates = find_candidate_profiles_for_job(db, posting)
        log.info("matching.candidates_found", job_posting_id=job_posting_id, count=len(candidates))

        for profile, similarity in candidates:
            match = upsert_match_similarity(db, profile.id, posting.id, similarity)
            if similarity >= SIMILARITY_FLOOR:
                explain_match(db, match, profile, posting)
        db.commit()
