from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.job import JobPostingOut


class MatchOut(BaseModel):
    id: UUID
    job_posting_id: UUID
    similarity_score: float
    llm_score: float | None
    explanation_text: str
    matched_skills: list[str]
    missing_skills: list[str]
    status: str
    computed_at: datetime | None
    job_posting: JobPostingOut

    model_config = {"from_attributes": True}
