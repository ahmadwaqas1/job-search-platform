"""RemoteOK (https://remoteok.com) - free, no API key. Docs/endpoint:
https://remoteok.com/api

Note: RemoteOK asks for a descriptive User-Agent and will occasionally
rate-limit; failures here just mean this source is skipped for the poll
cycle, they don't affect other sources.
"""
from datetime import datetime, timezone

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting
from app.utils.html_clean import strip_html

log = structlog.get_logger()

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "job-search-copilot (self-hosted; contact via app owner)"}


def _parse_posted_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except ValueError:
        return None


def _absolute_url(url: str) -> str:
    """RemoteOK sometimes returns a site-relative path instead of a full URL."""
    if url.startswith("/"):
        return f"https://remoteok.com{url}"
    return url


def _to_posting(job: dict) -> NormalizedJobPosting:
    url = _absolute_url(job.get("url", ""))
    has_salary = bool(job.get("salary_min"))

    return NormalizedJobPosting(
        external_id=str(job.get("id")),
        title=job.get("position", ""),
        company=job.get("company", ""),
        location=job.get("location") or "Remote",
        remote_type="remote",
        description_text=strip_html(job.get("description", "")),
        salary_min=job.get("salary_min"),
        salary_max=job.get("salary_max"),
        salary_currency="USD" if has_salary else "",
        salary_period="year" if has_salary else "",
        url=url,
        apply_url=job.get("apply_url") or url,
        posted_at=_parse_posted_at(job.get("date")),
        tags=job.get("tags") or [],
    )


class RemoteOKAdapter(JobSourceAdapter):
    source_type = "remoteok"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        params = {}
        if config.get("query"):
            params["tags"] = config["query"].replace(" ", "-").lower()

        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            try:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("remoteok.fetch_failed")
                return []

        # The API's first element is a legal/metadata notice, not a job.
        jobs = [j for j in resp.json() if isinstance(j, dict) and j.get("id")]
        return [_to_posting(job) for job in jobs]
