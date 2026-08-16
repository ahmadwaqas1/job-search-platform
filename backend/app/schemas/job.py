from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.job import JOB_SOURCE_TYPES


class JobSourceIn(BaseModel):
    type: str = Field(description=f"One of: {', '.join(JOB_SOURCE_TYPES)}")
    name: str
    config: dict = Field(default_factory=dict)
    poll_interval_minutes: int = 60
    is_active: bool = True


class JobSourceOut(BaseModel):
    id: UUID
    user_id: UUID | None
    type: str
    name: str
    config: dict
    poll_interval_minutes: int
    last_polled_at: datetime | None
    last_poll_status: str
    last_poll_error: str
    is_active: bool

    model_config = {"from_attributes": True}


class JobPostingOut(BaseModel):
    id: UUID
    title: str
    company: str
    location: str
    remote_type: str
    description_text: str
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    salary_period: str
    url: str
    apply_url: str
    posted_at: datetime | None
    tags: list[str]
    source_id: UUID

    model_config = {"from_attributes": True}
