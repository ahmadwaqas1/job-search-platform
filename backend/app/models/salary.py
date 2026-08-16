from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk


class SalarySnapshot(Base, UUIDPk, TimestampMixin):
    """A cached salary data point for a (role, location) pair, refreshed
    periodically by app/workers/salary_tasks.py. Multiple snapshots can
    exist per role/location (one per source) so the UI can show provenance
    and let low-coverage regions fall back to the aggregated-postings source.
    """

    __tablename__ = "salary_snapshots"

    role_title: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(30))  # adzuna|usajobs|bls|aggregated_postings
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    period: Mapped[str] = mapped_column(String(20), default="year")

    p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    median: Mapped[float | None] = mapped_column(Float, nullable=True)
    p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)

    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
