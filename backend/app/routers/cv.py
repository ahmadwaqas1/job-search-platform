import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.deps import get_current_user, get_db
from app.models.cv import CVDocument
from app.models.profile import Profile
from app.models.user import User
from app.schemas.cv import CVDocumentOut
from app.services.cv_export_service import AVAILABLE_TEMPLATES, render_profile_pdf
from app.services.profile_service import get_or_create_profile
from app.workers.queue import default_queue

router = APIRouter(prefix="/cv", tags=["cv"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/upload", response_model=CVDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"File exceeds {settings.max_upload_mb}MB limit.")

    profile = await get_or_create_profile(db, user)

    stored_name = f"{uuid.uuid4()}{suffix}"
    dest = settings.upload_path / stored_name
    dest.write_bytes(contents)

    doc = CVDocument(
        profile_id=profile.id,
        kind="uploaded",
        file_path=str(dest),
        original_filename=file.filename or stored_name,
        mime_type=file.content_type or "application/octet-stream",
        parse_status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    default_queue().enqueue("app.workers.cv_tasks.parse_cv_document", str(doc.id))
    return doc


@router.get("/documents", response_model=list[CVDocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    profile = await get_or_create_profile(db, user)
    stmt = (
        select(CVDocument)
        .where(CVDocument.profile_id == profile.id)
        .order_by(CVDocument.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.get("/documents/{document_id}", response_model=CVDocumentOut)
async def get_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    profile = await get_or_create_profile(db, user)
    doc = await db.get(CVDocument, document_id)
    if doc is None or doc.profile_id != profile.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV document not found.")
    return doc


@router.get("/export")
async def export_cv(
    template: str = Query("modern"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if template not in AVAILABLE_TEMPLATES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown template '{template}'.")

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
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found. Fill in your profile first.")

    pdf_bytes = render_profile_pdf(profile, template_id=template)
    filename = f"{(profile.full_name or 'resume').replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
