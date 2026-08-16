"""Salary estimate derived from Adzuna's live job-search results (reuses
the same endpoint as the Adzuna job source adapter, just aggregated into
percentiles here) rather than a separate salary-specific endpoint, since
that keeps this on the one Adzuna response shape we already handle
robustly elsewhere. Requires ADZUNA_APP_ID/ADZUNA_APP_KEY; returns None if
not configured or on any request failure - callers always have the
aggregated-postings fallback (see salary_service.py).
"""
import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()


async def fetch_adzuna_salary_estimate(role_title: str, location: str = "") -> dict | None:
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        return None

    country = settings.adzuna_country
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": 50,
        "what": role_title,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
        except httpx.HTTPError:
            log.warning("adzuna_salary.fetch_failed", role_title=role_title)
            return None

    values: list[float] = []
    for job in resp.json().get("results", []):
        smin, smax = job.get("salary_min"), job.get("salary_max")
        if smin and smax:
            values.append((smin + smax) / 2)
        elif smin or smax:
            values.append(smin or smax)

    if len(values) < 3:  # too little signal to call this a meaningful estimate
        return None

    values.sort()
    n = len(values)

    def pct(p: float) -> float:
        return values[min(n - 1, max(0, round(p * (n - 1))))]

    return {"p10": pct(0.10), "median": pct(0.50), "p90": pct(0.90), "sample_size": n, "currency": "USD" if country == "us" else ""}
