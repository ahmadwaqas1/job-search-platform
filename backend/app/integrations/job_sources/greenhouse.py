"""Greenhouse's public job board JSON API - every company using Greenhouse
exposes this unauthenticated at
https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
This is the same feed their own public career-page widget uses, not a
scrape - it's meant to be consumed by third parties. `config.board_token`
is the company's slug, e.g. "stripe", "airbnb" (found in their careers URL).
"""
from datetime import datetime

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting, infer_remote_type
from app.utils.html_clean import strip_html

log = structlog.get_logger()


class GreenhouseAdapter(JobSourceAdapter):
    source_type = "greenhouse"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        board_token = config.get("board_token")
        if not board_token:
            log.warning("greenhouse.missing_board_token")
            return []

        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, params={"content": "true"})
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("greenhouse.fetch_failed", board_token=board_token)
                return []

        results = []
        for job in resp.json().get("jobs", []):
            posted_at = None
            if job.get("updated_at"):
                try:
                    posted_at = datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            description = strip_html(job.get("content", ""))
            results.append(
                NormalizedJobPosting(
                    external_id=str(job.get("id")),
                    title=job.get("title", ""),
                    company=config.get("company_name", board_token),
                    location=(job.get("location") or {}).get("name", ""),
                    remote_type=infer_remote_type(job.get("title", ""), description),
                    description_text=description,
                    url=job.get("absolute_url", ""),
                    apply_url=job.get("absolute_url", ""),
                    posted_at=posted_at,
                    tags=[d.get("name", "") for d in job.get("departments", [])],
                )
            )
        return results
