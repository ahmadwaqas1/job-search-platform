"""Remotive (https://remotive.com) - free, no API key required.
Docs: https://remotive.com/api/remote-jobs
"""
from datetime import datetime

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting
from app.utils.html_clean import strip_html

log = structlog.get_logger()

API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveAdapter(JobSourceAdapter):
    source_type = "remotive"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        params = {}
        if config.get("query"):
            params["search"] = config["query"]
        if config.get("category"):
            params["category"] = config["category"]

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("remotive.fetch_failed")
                return []

        jobs = resp.json().get("jobs", [])
        results = []
        for job in jobs:
            posted_at = None
            if job.get("publication_date"):
                try:
                    posted_at = datetime.fromisoformat(job["publication_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            results.append(
                NormalizedJobPosting(
                    external_id=str(job.get("id")),
                    title=job.get("title", ""),
                    company=job.get("company_name", ""),
                    location=job.get("candidate_required_location", "Remote"),
                    remote_type="remote",
                    description_text=strip_html(job.get("description", "")),
                    url=job.get("url", ""),
                    apply_url=job.get("url", ""),
                    posted_at=posted_at,
                    tags=job.get("tags", []) or [],
                )
            )
        return results
