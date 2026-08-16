from uuid import UUID

import structlog

from app.database import get_sync_session
from app.models.application import Application
from app.models.job import JobPosting
from app.models.profile import Profile
from app.services.application_service import generate_draft_sync

log = structlog.get_logger()


def generate_application_draft(application_id: str) -> None:
    with get_sync_session() as db:
        application = db.get(Application, UUID(application_id))
        if application is None:
            log.warning("application.not_found", application_id=application_id)
            return

        posting = db.get(JobPosting, application.job_posting_id)
        profile = db.query(Profile).filter(Profile.user_id == application.user_id).one_or_none()
        if posting is None or profile is None:
            application.draft_status = "failed"
            db.commit()
            return

        generate_draft_sync(db, application, profile, posting)
