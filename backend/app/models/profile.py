from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPk

EMBED_DIM = get_settings().ollama_embed_dim


class Profile(Base, UUIDPk, TimestampMixin):
    """The canonical, user-confirmed job-search profile. This is the single
    source of truth used for matching and CV export - CV uploads only ever
    *pre-fill* this data via a review step, never write to it directly.
    """

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    full_name: Mapped[str] = mapped_column(String(255), default="")
    headline: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    links: Mapped[dict] = mapped_column(JSON, default=dict)  # {linkedin, github, website, ...}

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="profile")
    work_experience: Mapped[list["WorkExperience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="WorkExperience.order_index"
    )
    education: Mapped[list["Education"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Education.order_index"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Certification.order_index"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Project.order_index"
    )
    languages: Mapped[list["Language"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Language.order_index"
    )
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Skill.order_index"
    )
    cv_documents: Mapped[list["CVDocument"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )

    def searchable_text(self) -> str:
        """Flatten the profile into plain text for embedding generation."""
        parts = [self.headline, self.summary]
        parts += [f"{s.name}" for s in self.skills]
        parts += [
            f"{w.title} at {w.company}: {w.description}" for w in self.work_experience
        ]
        parts += [f"{e.degree} in {e.field_of_study}, {e.school}" for e in self.education]
        parts += [f"{p.name}: {p.description}" for p in self.projects]
        return "\n".join(p for p in parts if p)


class WorkExperience(Base, UUIDPk, TimestampMixin):
    __tablename__ = "work_experience"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="work_experience")


class Education(Base, UUIDPk, TimestampMixin):
    __tablename__ = "education"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    school: Mapped[str] = mapped_column(String(255), default="")
    degree: Mapped[str] = mapped_column(String(255), default="")
    field_of_study: Mapped[str] = mapped_column(String(255), default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="education")


class Certification(Base, UUIDPk, TimestampMixin):
    __tablename__ = "certifications"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    issuer: Mapped[str] = mapped_column(String(255), default="")
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_url: Mapped[str] = mapped_column(String(500), default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="certifications")


class Project(Base, UUIDPk, TimestampMixin):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    technologies: Mapped[str] = mapped_column(String(500), default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="projects")


class Language(Base, UUIDPk, TimestampMixin):
    __tablename__ = "languages"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    proficiency: Mapped[str] = mapped_column(String(50), default="")  # native/fluent/...
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="languages")


class Skill(Base, UUIDPk, TimestampMixin):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(150), default="")
    category: Mapped[str] = mapped_column(String(100), default="")  # e.g. "Languages", "Cloud"
    proficiency: Mapped[str] = mapped_column(String(50), default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="skills")
