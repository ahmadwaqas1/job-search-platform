"""Arbeitnow job board API (https://www.arbeitnow.com/api/job-board-api) -
free, no API key. Strong European/tech coverage. The public endpoint has no
keyword-search parameter, so when the source is configured with a `query`
we fetch a couple of pages and filter client-side on title/tags.
"""
from datetime import datetime, timezone

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting

log = structlog.get_logger()

API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 3


class ArbeitnowAdapter(JobSourceAdapter):
    source_type = "arbeitnow"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        query = (config.get("query") or "").lower().strip()
        results: list[NormalizedJobPosting] = []

        async with httpx.AsyncClient(timeout=30) as client:
            url = API_URL
            for _ in range(MAX_PAGES):
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    log.exception("arbeitnow.fetch_failed")
                    break

                payload = resp.json()
                for job in payload.get("data", []):
                    if query:
                        haystack = f"{job.get('title', '')} {' '.join(job.get('tags', []))}".lower()
                        if query not in haystack:
                            continue

                    posted_at = None
                    if job.get("created_at"):
                        try:
                            posted_at = datetime.fromtimestamp(int(job["created_at"]), tz=timezone.utc)
                        except (ValueError, OSError):
                            pass

                    results.append(
                        NormalizedJobPosting(
                            external_id=job.get("slug", ""),
                            title=job.get("title", ""),
                            company=job.get("company_name", ""),
                            location=job.get("location", ""),
                            remote_type="remote" if job.get("remote") else "onsite",
                            description_text=job.get("description", ""),
                            url=job.get("url", ""),
                            apply_url=job.get("url", ""),
                            posted_at=posted_at,
                            tags=job.get("tags", []) or [],
                        )
                    )

                next_url = (payload.get("links") or {}).get("next")
                if not next_url:
                    break
                url = next_url

        return results
