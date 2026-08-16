"""Adzuna job search API (https://developer.adzuna.com/) - free tier,
requires ADZUNA_APP_ID + ADZUNA_APP_KEY. Skipped by the scheduler entirely
if those aren't configured (see job_ingestion_service.poll_source).
"""
from datetime import datetime

import httpx
import structlog

from app.config import get_settings
from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting, infer_remote_type

log = structlog.get_logger()

settings = get_settings()


class AdzunaAdapter(JobSourceAdapter):
    source_type = "adzuna"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            log.info("adzuna.skipped_no_credentials")
            return []

        country = config.get("country", settings.adzuna_country)
        page = config.get("page", 1)
        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": 50,
            "content-type": "application/json",
        }
        if config.get("query"):
            params["what"] = config["query"]
        if config.get("location"):
            params["where"] = config["location"]

        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("adzuna.fetch_failed")
                return []

        results = []
        for job in resp.json().get("results", []):
            posted_at = None
            if job.get("created"):
                try:
                    posted_at = datetime.fromisoformat(job["created"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            description = job.get("description", "")
            results.append(
                NormalizedJobPosting(
                    external_id=str(job.get("id")),
                    title=job.get("title", ""),
                    company=(job.get("company") or {}).get("display_name", ""),
                    location=(job.get("location") or {}).get("display_name", ""),
                    remote_type=infer_remote_type(job.get("title", ""), description),
                    description_text=description,
                    salary_min=job.get("salary_min"),
                    salary_max=job.get("salary_max"),
                    salary_currency="",  # Adzuna's search endpoint doesn't return currency directly
                    salary_period="year",
                    url=job.get("redirect_url", ""),
                    apply_url=job.get("redirect_url", ""),
                    posted_at=posted_at,
                    tags=[c.get("label") for c in [job.get("category") or {}] if c.get("label")],
                )
            )
        return results
