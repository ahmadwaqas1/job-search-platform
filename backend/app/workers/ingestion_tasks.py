from uuid import UUID

import structlog

from app.database import get_sync_session
from app.models.job import JobSource
from app.services.job_ingestion_service import poll_source_sync

log = structlog.get_logger()


def poll_source(job_source_id: str) -> None:
    with get_sync_session() as db:
        source = db.get(JobSource, UUID(job_source_id))
        if source is None:
            log.warning("ingestion.source_not_found", job_source_id=job_source_id)
            return
        if not source.is_active:
            return
        poll_source_sync(db, source)
