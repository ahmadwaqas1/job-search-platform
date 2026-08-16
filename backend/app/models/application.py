from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk

APPLICATION_STATUSES = ("saved", "applied", "interviewing", "offer", "rejected", "withdrawn")


class Application(Base, UUIDPk, TimestampMixin):
    """A job the user is tracking, from an AI-drafted application through
    to an outcome. Draft generation never auto-submits anywhere - status
    only moves to 'applied' when the user confirms it themselves.
    """

    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE")
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(20), default="saved")

    draft_status: Mapped[str] = mapped_column(
        String(20), default="none"
    )  # none|generating|ready|failed
    tailored_resume_cv_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cv_documents.id", ondelete="SET NULL"), nullable=True
    )
    cover_letter_text: Mapped[str] = mapped_column(Text, default="")
    application_answers: Mapped[list[dict]] = mapped_column(JSON, default=list)  # [{question, answer}]

    applied_via: Mapped[str] = mapped_column(String(20), default="manual")  # manual|auto_api
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    job_posting: Mapped["JobPosting"] = relationship()
    events: Mapped[list["ApplicationEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.created_at"
    )


class ApplicationEvent(Base, UUIDPk, TimestampMixin):
    """Kanban audit trail: one row per status transition or note."""

    __tablename__ = "application_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    event_type: Mapped[str] = mapped_column(String(30), default="status_change")
    from_status: Mapped[str] = mapped_column(String(20), default="")
    to_status: Mapped[str] = mapped_column(String(20), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    application: Mapped["Application"] = relationship(back_populates="events")
