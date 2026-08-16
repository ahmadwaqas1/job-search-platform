"""RQ tasks that keep profile/job embeddings up to date. RQ workers are
synchronous processes, so each task wraps its async Ollama call with
asyncio.run() and uses the sync DB session (see app/database.py).
"""
import asyncio
from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.database import get_sync_session
from app.integrations.ollama_client import OllamaClient
from app.models.job import JobPosting
from app.models.profile import Profile
from app.workers.matching_tasks import find_and_score_matches_for_job, find_and_score_matches_for_profile

log = structlog.get_logger()


def generate_profile_embedding(profile_id: str) -> None:
    """Step 1 of the matching pipeline (see services/matching_service.py
    for the full picture): turn the profile's text into a vector, save it,
    then immediately kick off step 2 (pgvector candidate search) for this
    profile. Runs as an RQ task, enqueued whenever a profile is saved.
    """
    with get_sync_session() as db:
        profile = db.get(Profile, UUID(profile_id))
        if profile is None:
            log.warning("embedding.profile_not_found", profile_id=profile_id)
            return

        text = profile.searchable_text()
        if not text.strip():
            return

        client = OllamaClient()
        vector = asyncio.run(client.embed(text))

        profile.embedding = vector
        profile.embedding_updated_at = datetime.now(timezone.utc)
        db.commit()

    find_and_score_matches_for_profile(profile_id)


def generate_job_embedding(job_posting_id: str) -> None:
    """Same as generate_profile_embedding above, but for one job posting -
    enqueued whenever a posting is newly ingested or its content changes.
    """
    with get_sync_session() as db:
        posting = db.get(JobPosting, UUID(job_posting_id))
        if posting is None:
            log.warning("embedding.job_not_found", job_posting_id=job_posting_id)
            return

        text = posting.searchable_text()
        if not text.strip():
            return

        client = OllamaClient()
        vector = asyncio.run(client.embed(text))

        posting.embedding = vector
        posting.embedding_updated_at = datetime.now(timezone.utc)
        db.commit()

    find_and_score_matches_for_job(job_posting_id)
