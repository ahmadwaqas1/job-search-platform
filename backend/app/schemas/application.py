from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.job import JobPostingOut


class ApplicationAnswer(BaseModel):
    question: str
    answer: str


class ApplicationCreate(BaseModel):
    job_posting_id: UUID
    match_id: UUID | None = None
    auto_generate_draft: bool = True


class ApplicationStatusUpdate(BaseModel):
    status: str
    note: str = ""


class ApplicationEdit(BaseModel):
    cover_letter_text: str | None = None
    application_answers: list[ApplicationAnswer] | None = None
    notes: str | None = None


class ApplicationEventOut(BaseModel):
    id: UUID
    event_type: str
    from_status: str
    to_status: str
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationOut(BaseModel):
    id: UUID
    status: str
    draft_status: str
    cover_letter_text: str
    application_answers: list[dict]
    applied_via: str
    applied_at: datetime | None
    notes: str
    tailored_resume_cv_document_id: UUID | None
    job_posting: JobPostingOut
    events: list[ApplicationEventOut]
    created_at: datetime

    model_config = {"from_attributes": True}
