from datetime import datetime

from pydantic import BaseModel


class SalarySnapshotOut(BaseModel):
    role_title: str
    location: str
    source: str
    currency: str
    period: str
    p10: float | None
    median: float | None
    p90: float | None
    sample_size: int
    fetched_at: datetime | None

    model_config = {"from_attributes": True}
