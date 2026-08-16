"""Application tracker + AI draft generation.

Auto-apply is review-then-submit only: draft generation produces a tailored
resume variant, a cover letter, and draft answers to common application
questions - all sitting in `status="saved"` until the user reviews them and
marks the application as actually submitted themselves (`status="applied"`).
Nothing in this module ever calls out to a job board to submit anything.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from app.integrations.ollama_client import OllamaClient
from app.models.application import Application, ApplicationEvent
from app.models.cv import CVDocument
from app.models.job import JobPosting
from app.models.profile import Profile

log = structlog.get_logger()

VALID_STATUSES = ("saved", "applied", "interviewing", "offer", "rejected", "withdrawn")

DRAFT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "tailored_summary": {"type": "string"},
        "emphasized_skills": {"type": "array", "items": {"type": "string"}},
        "cover_letter": {"type": "string"},
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"question": {"type": "string"}, "answer": {"type": "string"}},
                "required": ["question", "answer"],
            },
        },
    },
    "required": ["tailored_summary", "emphasized_skills", "cover_letter", "answers"],
}

DRAFT_SYSTEM_PROMPT = (
    "You are a job-application assistant helping a candidate prepare materials for a "
    "specific job posting. Using ONLY the candidate's real profile data, produce: "
    "(1) tailored_summary - a 2-4 sentence professional summary emphasizing experience "
    "most relevant to this job, (2) emphasized_skills - a subset of the candidate's "
    "existing skills (use their exact names) most relevant to this role, (3) cover_letter "
    "- a personalized 3-4 paragraph cover letter addressed to the hiring team at the "
    "actual company, professional tone, no unfilled placeholders, (4) answers - draft "
    "answers to 3-4 common application questions relevant to this role (e.g. why "
    "interested, relevant experience, availability). NEVER invent employers, titles, "
    "dates, or skills that are not present in the candidate's profile - if the candidate "
    "is missing something the job wants, do not claim they have it. Respond with ONLY "
    "JSON matching the schema."
)


# --- draft generation (sync, called from RQ worker) ------------------------


async def _generate_draft_async(profile: Profile, posting: JobPosting) -> dict:
    client = OllamaClient()
    user_prompt = (
        f"CANDIDATE PROFILE:\n{profile.searchable_text()[:4000]}\n\n"
        f"JOB POSTING:\nTitle: {posting.title}\nCompany: {posting.company}\n"
        f"Location: {posting.location}\n\n{posting.description_text[:4000]}"
    )
    return await client.generate_json(DRAFT_SYSTEM_PROMPT, user_prompt, DRAFT_JSON_SCHEMA)


def generate_draft_sync(db: Session, application: Application, profile: Profile, posting: JobPosting) -> None:
    import asyncio

    application.draft_status = "generating"
    db.commit()

    try:
        result = asyncio.run(_generate_draft_async(profile, posting))

        tailored_doc = CVDocument(
            profile_id=profile.id,
            kind="generated",
            parse_status="parsed",
            parsed_json={
                "tailored_summary": result.get("tailored_summary", ""),
                "emphasized_skills": result.get("emphasized_skills", []),
                "for_job_posting_id": str(posting.id),
            },
        )
        db.add(tailored_doc)
        db.flush()

        application.tailored_resume_cv_document_id = tailored_doc.id
        application.cover_letter_text = result.get("cover_letter", "")
        application.application_answers = result.get("answers", [])
        application.draft_status = "ready"
        db.commit()
    except Exception:
        log.exception("application.draft_generation_failed", application_id=str(application.id))
        application.draft_status = "failed"
        db.commit()


# --- async CRUD for the router ---------------------------------------------


def _eager_opts():
    return (selectinload(Application.job_posting), selectinload(Application.events))


async def create_application(
    db: AsyncSession, user_id: UUID, job_posting_id: UUID, match_id: UUID | None
) -> Application:
    application = Application(user_id=user_id, job_posting_id=job_posting_id, match_id=match_id)
    db.add(application)
    db.add(ApplicationEvent(application=application, event_type="created", to_status="saved"))
    await db.commit()
    stmt = select(Application).where(Application.id == application.id).options(*_eager_opts())
    return (await db.execute(stmt)).scalar_one()


async def list_applications(db: AsyncSession, user_id: UUID, status_filter: str | None = None) -> list[Application]:
    stmt = select(Application).where(Application.user_id == user_id).options(*_eager_opts())
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)
    stmt = stmt.order_by(Application.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_application(db: AsyncSession, user_id: UUID, application_id: UUID) -> Application | None:
    stmt = (
        select(Application)
        .where(Application.id == application_id, Application.user_id == user_id)
        .options(*_eager_opts())
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_status(
    db: AsyncSession, application: Application, new_status: str, note: str = ""
) -> Application:
    old_status = application.status
    application.status = new_status
    if new_status == "applied" and application.applied_at is None:
        application.applied_at = datetime.now(timezone.utc)
    db.add(
        ApplicationEvent(
            application_id=application.id,
            event_type="status_change",
            from_status=old_status,
            to_status=new_status,
            note=note,
        )
    )
    await db.commit()
    stmt = select(Application).where(Application.id == application.id).options(*_eager_opts())
    return (await db.execute(stmt)).scalar_one()


async def edit_application(
    db: AsyncSession,
    application: Application,
    cover_letter_text: str | None,
    application_answers: list[dict] | None,
    notes: str | None,
) -> Application:
    if cover_letter_text is not None:
        application.cover_letter_text = cover_letter_text
    if application_answers is not None:
        application.application_answers = application_answers
    if notes is not None:
        application.notes = notes
    await db.commit()
    stmt = select(Application).where(Application.id == application.id).options(*_eager_opts())
    return (await db.execute(stmt)).scalar_one()
