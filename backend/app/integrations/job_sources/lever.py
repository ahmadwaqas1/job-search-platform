"""Lever's public postings API - every company on Lever exposes this
unauthenticated at https://api.lever.co/v0/postings/{company}?mode=json,
the same feed powering their own public careers page. `config.company` is
the company's Lever slug.
"""
from datetime import datetime, timezone

import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting, infer_remote_type
from app.utils.html_clean import strip_html

log = structlog.get_logger()


class LeverAdapter(JobSourceAdapter):
    source_type = "lever"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        company = config.get("company")
        if not company:
            log.warning("lever.missing_company")
            return []

        url = f"https://api.lever.co/v0/postings/{company}"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, params={"mode": "json"})
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("lever.fetch_failed", company=company)
                return []

        results = []
        for job in resp.json():
            posted_at = None
            if job.get("createdAt"):
                try:
                    posted_at = datetime.fromtimestamp(int(job["createdAt"]) / 1000, tz=timezone.utc)
                except (ValueError, OSError):
                    pass

            categories = job.get("categories", {}) or {}
            description = strip_html(job.get("descriptionPlain") or job.get("description", ""))
            results.append(
                NormalizedJobPosting(
                    external_id=str(job.get("id")),
                    title=job.get("text", ""),
                    company=config.get("company_name", company),
                    location=categories.get("location", ""),
                    remote_type=infer_remote_type(categories.get("location", ""), job.get("text", "")),
                    description_text=description,
                    url=job.get("hostedUrl", ""),
                    apply_url=job.get("applyUrl", job.get("hostedUrl", "")),
                    posted_at=posted_at,
                    tags=[t for t in [categories.get("team"), categories.get("commitment")] if t],
                )
            )
        return results
