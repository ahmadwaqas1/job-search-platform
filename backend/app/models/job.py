from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk

EMBED_DIM = get_settings().ollama_embed_dim

# Source types the ingestion pipeline knows how to poll. See
# app/integrations/job_sources/ for the adapter implementing each one.
JOB_SOURCE_TYPES = (
    "adzuna",
    "remotive",
    "remoteok",
    "arbeitnow",
    "usajobs",
    "themuse",
    "greenhouse",
    "lever",
    "custom_rss",
)


class JobSource(Base, UUIDPk, TimestampMixin):
    """A configured job feed - either one of the built-in aggregator APIs
    (global, user_id NULL, seeded once) or a user-added regional link/RSS
    feed (user_id set).
    """

    __tablename__ = "job_sources"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"query": "python developer", "url": "..."}
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_poll_status: Mapped[str] = mapped_column(String(20), default="never_run")
    last_poll_error: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    postings: Mapped[list["JobPosting"]] = relationship(back_populates="source")


class JobPosting(Base, UUIDPk, TimestampMixin):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_source_external_id"),)

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="CASCADE")
    )
    external_id: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    remote_type: Mapped[str] = mapped_column(String(30), default="unknown")  # remote|hybrid|onsite|unknown
    description_text: Mapped[str] = mapped_column(Text, default="")
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="")
    salary_period: Mapped[str] = mapped_column(String(20), default="")  # year|month|hour
    url: Mapped[str] = mapped_column(String(1000), default="")
    apply_url: Mapped[str] = mapped_column(String(1000), default="")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    content_hash: Mapped[str] = mapped_column(String(64), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped["JobSource"] = relationship(back_populates="postings")

    def searchable_text(self) -> str:
        return f"{self.title} at {self.company} ({self.location})\n{self.description_text}"
