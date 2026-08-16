from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.deps import get_current_user, get_db
from app.models.cv import CVDocument
from app.models.profile import Profile
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationEdit,
    ApplicationOut,
    ApplicationStatusUpdate,
)
from app.services import application_service
from app.services.cv_export_service import render_tailored_pdf
from app.workers.queue import llm_queue

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await application_service.list_applications(db, user.id, status_filter)


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    application = await application_service.create_application(
        db, user.id, payload.job_posting_id, payload.match_id
    )
    if payload.auto_generate_draft:
        llm_queue().enqueue("app.workers.generation_tasks.generate_application_draft", str(application.id))
    return application


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    application = await application_service.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    return application


@router.post("/{application_id}/generate-draft", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_draft(
    application_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    application = await application_service.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    llm_queue().enqueue("app.workers.generation_tasks.generate_application_draft", str(application_id))
    return {"status": "queued"}


@router.patch("/{application_id}/status", response_model=ApplicationOut)
async def update_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.status not in application_service.VALID_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"status must be one of {application_service.VALID_STATUSES}")
    application = await application_service.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    return await application_service.update_status(db, application, payload.status, payload.note)


@router.patch("/{application_id}", response_model=ApplicationOut)
async def edit_application(
    application_id: UUID,
    payload: ApplicationEdit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = await application_service.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    answers = [a.model_dump() for a in payload.application_answers] if payload.application_answers is not None else None
    return await application_service.edit_application(
        db, application, payload.cover_letter_text, answers, payload.notes
    )


@router.get("/{application_id}/resume.pdf")
async def download_tailored_resume(
    application_id: UUID,
    template: str = Query("modern"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    application = await application_service.get_application(db, user.id, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    if application.tailored_resume_cv_document_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No tailored resume has been generated yet.")

    tailored_doc = await db.get(CVDocument, application.tailored_resume_cv_document_id)
    stmt = (
        select(Profile)
        .where(Profile.user_id == user.id)
        .options(
            selectinload(Profile.work_experience),
            selectinload(Profile.education),
            selectinload(Profile.certifications),
            selectinload(Profile.projects),
            selectinload(Profile.languages),
            selectinload(Profile.skills),
        )
    )
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None or tailored_doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile or tailored resume data not found.")

    parsed = tailored_doc.parsed_json or {}
    pdf_bytes = render_tailored_pdf(
        profile,
        tailored_summary=parsed.get("tailored_summary", ""),
        emphasized_skills=parsed.get("emphasized_skills", []),
        template_id=template,
    )
    filename = f"{(profile.full_name or 'resume').replace(' ', '_')}_tailored.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
