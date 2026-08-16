"""The Muse public jobs API (https://www.themuse.com/developers/api/v2) -
free, no API key. Filters by category/company/location rather than a
free-text keyword, so `config.query` is matched client-side against the
category list as a best effort.
"""
from datetime import datetime

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting
from app.utils.html_clean import strip_html

log = structlog.get_logger()

API_URL = "https://www.themuse.com/api/public/jobs"
DEFAULT_TECH_CATEGORY = "Engineering"


class TheMuseAdapter(JobSourceAdapter):
    source_type = "themuse"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        params = {"category": config.get("category", DEFAULT_TECH_CATEGORY), "page": config.get("page", 0)}
        if config.get("location"):
            params["location"] = config["location"]

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("themuse.fetch_failed")
                return []

        results = []
        for job in resp.json().get("results", []):
            posted_at = None
            if job.get("publication_date"):
                try:
                    posted_at = datetime.fromisoformat(job["publication_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            locations = job.get("locations") or []
            location = ", ".join(loc.get("name", "") for loc in locations if loc.get("name")) or "Unspecified"

            results.append(
                NormalizedJobPosting(
                    external_id=str(job.get("id")),
                    title=job.get("name", ""),
                    company=(job.get("company") or {}).get("name", ""),
                    location=location,
                    remote_type="remote" if "remote" in location.lower() else "onsite",
                    description_text=strip_html(job.get("contents", "")),
                    url=(job.get("refs") or {}).get("landing_page", ""),
                    apply_url=(job.get("refs") or {}).get("landing_page", ""),
                    posted_at=posted_at,
                    tags=[c.get("name") for c in job.get("categories", []) if c.get("name")],
                )
            )
        return results
