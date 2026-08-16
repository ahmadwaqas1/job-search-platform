from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk


class Match(Base, UUIDPk, TimestampMixin):
    """A precomputed profile<->job match. Read paths only ever query this
    table - nothing calls the LLM synchronously on page load. See
    app/services/matching_service.py for how rows here get produced.
    """

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("profile_id", "job_posting_id", name="uq_profile_job"),)

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE")
    )

    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)  # raw pgvector cosine similarity
    llm_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100, LLM-judged fit
    explanation_text: Mapped[str] = mapped_column(Text, default="")
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(20), default="new")  # new|reviewed|dismissed
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job_posting: Mapped["JobPosting"] = relationship()
