"""User-added regional/niche job boards, added in Settings as an RSS/Atom
feed URL. Deliberately RSS/Atom only - not a generic HTML scraper - so this
stays a polite, public-feed integration rather than something that could
drift into scraping login-walled or ToS-restricted pages.
"""
from datetime import timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
import structlog

from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting, infer_remote_type
from app.utils.html_clean import strip_html

log = structlog.get_logger()


class CustomRSSAdapter(JobSourceAdapter):
    source_type = "custom_rss"

    async def fetch(self, config: dict) -> list[NormalizedJobPosting]:
        feed_url = config.get("feed_url")
        if not feed_url:
            log.warning("custom_rss.missing_feed_url")
            return []

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    feed_url, headers={"User-Agent": "job-search-copilot (self-hosted RSS reader)"}
                )
                resp.raise_for_status()
            except httpx.HTTPError:
                log.exception("custom_rss.fetch_failed", feed_url=feed_url)
                return []

        parsed = feedparser.parse(resp.content)
        results = []
        for entry in parsed.entries:
            posted_at = None
            if entry.get("published"):
                try:
                    posted_at = parsedate_to_datetime(entry["published"])
                    if posted_at.tzinfo is None:
                        posted_at = posted_at.replace(tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    pass

            description = strip_html(entry.get("summary", ""))
            title = entry.get("title", "")
            results.append(
                NormalizedJobPosting(
                    external_id=entry.get("id") or entry.get("link", title),
                    title=title,
                    company=config.get("company_name", ""),
                    location=config.get("location", ""),
                    remote_type=infer_remote_type(title, description),
                    description_text=description,
                    url=entry.get("link", ""),
                    apply_url=entry.get("link", ""),
                    posted_at=posted_at,
                    tags=[t.get("term") for t in entry.get("tags", []) if t.get("term")],
                )
            )
        return results
