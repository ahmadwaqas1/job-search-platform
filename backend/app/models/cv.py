from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk


class CVDocument(Base, UUIDPk, TimestampMixin):
    """An uploaded resume file (source for AI extraction) or a generated
    export (tailored resume produced for a specific application).
    """

    __tablename__ = "cv_documents"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded | generated
    file_path: Mapped[str] = mapped_column(String(1000), default="")
    original_filename: Mapped[str] = mapped_column(String(500), default="")
    mime_type: Mapped[str] = mapped_column(String(100), default="")

    parse_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending | processing | parsed | failed
    parse_error: Mapped[str] = mapped_column(Text, default="")
    raw_extracted_text: Mapped[str] = mapped_column(Text, default="")
    parsed_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    template_id: Mapped[str] = mapped_column(String(50), default="")

    profile: Mapped["Profile"] = relationship(back_populates="cv_documents")
