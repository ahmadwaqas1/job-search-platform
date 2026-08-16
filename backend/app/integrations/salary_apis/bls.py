"""US Bureau of Labor Statistics (BLS) Occupational Employment and Wage
Statistics, via the public timeseries API (https://www.bls.gov/developers/).
Works unauthenticated at low rate limits; set BLS_API_KEY for the higher
v2 registered request limits.

Mapping a free-text role title to BLS data requires the exact OES series ID
for that occupation, which BLS builds from a specific area/industry/SOC/
datatype code combination - getting this wrong silently returns empty data
rather than wrong data (BLS rejects malformed series IDs), but it's still
not something to guess at. ROLE_TO_SERIES ships empty on purpose: this
integration is an opt-in extension point, not a curated-out-of-the-box
source like Adzuna/aggregated-postings. To enable it for a role, look up
the correct series ID for the occupation's national data via BLS's own
OES query tool (https://data.bls.gov/oes/#/home) or series ID directory
(https://download.bls.gov/pub/time.series/oe/oe.txt) and add it below,
e.g. ROLE_TO_SERIES["software"] = "OEUN......".
"""
import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# role keyword (lowercased, matched via substring) -> verified BLS OES
# series ID for the national mean wage of that occupation. Empty by
# default - see module docstring for how to populate this.
ROLE_TO_SERIES: dict[str, str] = {}


def _lookup_series(role_title: str) -> str | None:
    role = role_title.lower()
    for keyword, series_id in ROLE_TO_SERIES.items():
        if keyword in role:
            return series_id
    return None


async def fetch_bls_wage_estimate(role_title: str) -> dict | None:
    series_id = _lookup_series(role_title)
    if series_id is None:
        return None

    payload: dict = {"seriesid": [series_id]}
    if settings.bls_api_key:
        payload["registrationkey"] = settings.bls_api_key

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.post(BLS_API_URL, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError:
            log.warning("bls.fetch_failed", role_title=role_title, series_id=series_id)
            return None

    data = resp.json()
    try:
        series = data["Results"]["series"][0]["data"]
        if not series:
            return None
        latest = series[0]  # BLS returns newest first
        mean_wage = float(latest["value"])
    except (KeyError, IndexError, ValueError, TypeError):
        log.warning("bls.unexpected_response_shape", role_title=role_title)
        return None

    # OES gives a mean, not percentiles - approximate a band around it
    # rather than presenting a single point as if it were a distribution.
    return {
        "p10": round(mean_wage * 0.75, 2),
        "median": mean_wage,
        "p90": round(mean_wage * 1.35, 2),
        "sample_size": 0,
        "currency": "USD",
    }
