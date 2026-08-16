"""USAJobs API (https://developer.usajobs.gov/) - US federal government
listings, free, requires an API key + a registered user-agent email.
Skipped entirely if USAJOBS_API_KEY isn't configured.
"""
from datetime import datetime

import httpx
import structlog

from app.config import get_settings
from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting

log = structlog.get_logger()

settings = get_settings()

API_URL = "https://data.usajobs.gov/api/search"

# USAJobs' pay-rate codes -> our salary_period values.
PAY_PERIOD_BY_CODE = {"PA": "year", "PH": "hour", "PM": "month"}


def _parse_posted_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_salary(descriptor: dict) -> tuple[float | None, float | None, str]:
    """USAJobs nests pay info as a one-item list; pull the min/max/period
    out of it, defaulting to "no salary info" if the list is empty.
    """
    pay = (descriptor.get("PositionRemuneration") or [{}])[0]
    salary_min = float(pay["MinimumRange"]) if pay.get("MinimumRange") else None
    salary_max = float(pay["MaximumRange"]) if pay.get("MaximumRange") else None
    period = PAY_PERIOD_BY_CODE.get(pay.get("RateIntervalCode", ""), "year")
    return salary_min, salary_max, period


def _job_summary(descriptor: dict) -> str:
    user_area = descriptor.get("UserArea") or {}
    details = user_area.get("Details") or {}
    return details.get("JobSummary", "")


def _apply_url(descriptor: dict) -> str:
    """USAJobs returns ApplyURI as a list (sometimes empty); fall back to
    the posting's own URL if there's no separate apply link.
    """
    apply_uris = descriptor.get("ApplyURI") or []
    if apply_uris:
        return apply_uris[0]
    return descriptor.get("PositionURI", "")


def _to_posting(item: dict) -> NormalizedJobPosting:
    descriptor = item.get("MatchedObjectDescriptor", {})
    salary_min, salary_max, period = _parse_salary(descriptor)

    return NormalizedJobPosting(
        external_id=str(descriptor.get("PositionID") or item.get("MatchedObjectId", "")),
        title=descriptor.get("PositionTitle", ""),
        company=descriptor.get("OrganizationName", ""),
        location=descriptor.get("PositionLocationDisplay", ""),
        remote_type="onsite",
        description_text=_job_summary(descriptor),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD",
        salary_period=period,
        url=descriptor.get("PositionURI", ""),
        apply_url=_apply_url(descriptor),
        posted_at=_parse_posted_at(descriptor.get("PublicationStartDate")),
        tags=[],
    )


class USAJobsAdapter(JobSourceAdapter):
    source_type = "usajobs"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        if not settings.usajobs_api_key or not settings.usajobs_user_agent:
            log.info("usajobs.skipped_no_credentials")
            return []

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": settings.usajobs_user_agent,
            "Authorization-Key": settings.usajobs_api_key,
        }
        params = {"ResultsPerPage": 50}
        if config.get("query"):
            params["Keyword"] = config["query"]
        if config.get("location"):
            params["LocationName"] = config["location"]

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            try:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("usajobs.fetch_failed")
                return []

        items = resp.json().get("SearchResult", {}).get("SearchResultItems", [])
        return [_to_posting(item) for item in items]
