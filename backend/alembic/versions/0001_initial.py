"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-16
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.config import get_settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBED_DIM = get_settings().ollama_embed_dim


def _uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "profiles",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), server_default="", nullable=False),
        sa.Column("headline", sa.String(255), server_default="", nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("phone", sa.String(50), server_default="", nullable=False),
        sa.Column("email", sa.String(255), server_default="", nullable=False),
        sa.Column("links", postgresql.JSON(), server_default="{}", nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.execute(
        "CREATE INDEX ix_profiles_embedding ON profiles USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "work_experience",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), server_default="", nullable=False),
        sa.Column("company", sa.String(255), server_default="", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "education",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school", sa.String(255), server_default="", nullable=False),
        sa.Column("degree", sa.String(255), server_default="", nullable=False),
        sa.Column("field_of_study", sa.String(255), server_default="", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "certifications",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), server_default="", nullable=False),
        sa.Column("issuer", sa.String(255), server_default="", nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("credential_url", sa.String(500), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "projects",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), server_default="", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("url", sa.String(500), server_default="", nullable=False),
        sa.Column("technologies", sa.String(500), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "languages",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), server_default="", nullable=False),
        sa.Column("proficiency", sa.String(50), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "skills",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), server_default="", nullable=False),
        sa.Column("category", sa.String(100), server_default="", nullable=False),
        sa.Column("proficiency", sa.String(50), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "cv_documents",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), server_default="uploaded", nullable=False),
        sa.Column("file_path", sa.String(1000), server_default="", nullable=False),
        sa.Column("original_filename", sa.String(500), server_default="", nullable=False),
        sa.Column("mime_type", sa.String(100), server_default="", nullable=False),
        sa.Column("parse_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("parse_error", sa.Text(), server_default="", nullable=False),
        sa.Column("raw_extracted_text", sa.Text(), server_default="", nullable=False),
        sa.Column("parsed_json", postgresql.JSON(), nullable=True),
        sa.Column("template_id", sa.String(50), server_default="", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "job_sources",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", postgresql.JSON(), server_default="{}", nullable=False),
        sa.Column("poll_interval_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_poll_status", sa.String(20), server_default="never_run", nullable=False),
        sa.Column("last_poll_error", sa.Text(), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "job_postings",
        _uuid_pk(),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), server_default="", nullable=False),
        sa.Column("company", sa.String(255), server_default="", nullable=False),
        sa.Column("location", sa.String(255), server_default="", nullable=False),
        sa.Column("remote_type", sa.String(30), server_default="unknown", nullable=False),
        sa.Column("description_text", sa.Text(), server_default="", nullable=False),
        sa.Column("salary_min", sa.Float(), nullable=True),
        sa.Column("salary_max", sa.Float(), nullable=True),
        sa.Column("salary_currency", sa.String(10), server_default="", nullable=False),
        sa.Column("salary_period", sa.String(20), server_default="", nullable=False),
        sa.Column("url", sa.String(1000), server_default="", nullable=False),
        sa.Column("apply_url", sa.String(1000), server_default="", nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.JSON(), server_default="[]", nullable=False),
        sa.Column("content_hash", sa.String(64), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("embedding_updated_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("source_id", "external_id", name="uq_source_external_id"),
    )
    op.create_index("ix_job_postings_title", "job_postings", ["title"])
    op.create_index("ix_job_postings_location", "job_postings", ["location"])
    op.execute(
        "CREATE INDEX ix_job_postings_embedding ON job_postings USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "matches",
        _uuid_pk(),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_posting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("llm_score", sa.Float(), nullable=True),
        sa.Column("explanation_text", sa.Text(), server_default="", nullable=False),
        sa.Column("matched_skills", postgresql.JSON(), server_default="[]", nullable=False),
        sa.Column("missing_skills", postgresql.JSON(), server_default="[]", nullable=False),
        sa.Column("status", sa.String(20), server_default="new", nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("profile_id", "job_posting_id", name="uq_profile_job"),
    )

    op.create_table(
        "applications",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_posting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="saved", nullable=False),
        sa.Column("draft_status", sa.String(20), server_default="none", nullable=False),
        sa.Column("tailored_resume_cv_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cv_documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cover_letter_text", sa.Text(), server_default="", nullable=False),
        sa.Column("application_answers", postgresql.JSON(), server_default="[]", nullable=False),
        sa.Column("applied_via", sa.String(20), server_default="manual", nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "application_events",
        _uuid_pk(),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(30), server_default="status_change", nullable=False),
        sa.Column("from_status", sa.String(20), server_default="", nullable=False),
        sa.Column("to_status", sa.String(20), server_default="", nullable=False),
        sa.Column("note", sa.Text(), server_default="", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "salary_snapshots",
        _uuid_pk(),
        sa.Column("role_title", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("period", sa.String(20), server_default="year", nullable=False),
        sa.Column("p10", sa.Float(), nullable=True),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("p90", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), server_default="0", nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_salary_snapshots_role_title", "salary_snapshots", ["role_title"])
    op.create_index("ix_salary_snapshots_location", "salary_snapshots", ["location"])

    op.create_table(
        "chat_sessions",
        _uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), server_default="New conversation", nullable=False),
        sa.Column("job_posting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )

    op.create_table(
        "chat_messages",
        _uuid_pk(),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", postgresql.JSON(), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_index("ix_salary_snapshots_location", table_name="salary_snapshots")
    op.drop_index("ix_salary_snapshots_role_title", table_name="salary_snapshots")
    op.drop_table("salary_snapshots")
    op.drop_table("application_events")
    op.drop_table("applications")
    op.drop_table("matches")
    op.execute("DROP INDEX IF EXISTS ix_job_postings_embedding")
    op.drop_index("ix_job_postings_location", table_name="job_postings")
    op.drop_index("ix_job_postings_title", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_table("job_sources")
    op.drop_table("cv_documents")
    op.drop_table("skills")
    op.drop_table("languages")
    op.drop_table("projects")
    op.drop_table("certifications")
    op.drop_table("education")
    op.drop_table("work_experience")
    op.execute("DROP INDEX IF EXISTS ix_profiles_embedding")
    op.drop_table("profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
