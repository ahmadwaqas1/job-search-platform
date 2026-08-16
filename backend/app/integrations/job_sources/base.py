"""Common interface every job-source adapter implements. Each adapter only
does normalization + fetching for its source's own API - upserting into
job_postings and change-detection hashing lives in
app/services/job_ingestion_service.py, shared across all of them.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedJobPosting:
    external_id: str
    title: str
    company: str = ""
    location: str = ""
    remote_type: str = "unknown"  # remote | hybrid | onsite | unknown
    description_text: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = ""
    salary_period: str = ""  # year | month | hour
    url: str = ""
    apply_url: str = ""
    posted_at: datetime | None = None
    tags: list[str] = field(default_factory=list)


class JobSourceAdapter(ABC):
    source_type: str

    @abstractmethod
    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        """Fetch postings for a single configured source. `config` is the
        job_sources.config JSON blob (query keywords, location, feed URL,
        etc, depending on the adapter). Should raise on hard failures and
        return [] for "no results" - the caller records success/failure
        either way and never crashes the whole polling sweep.
        """
        raise NotImplementedError


def infer_remote_type(*texts: str) -> str:
    blob = " ".join(t or "" for t in texts).lower()
    if "remote" in blob:
        return "remote"
    if "hybrid" in blob:
        return "hybrid"
    if blob.strip():
        return "onsite"
    return "unknown"
