from app.integrations.job_sources.adzuna import AdzunaAdapter
from app.integrations.job_sources.arbeitnow import ArbeitnowAdapter
from app.integrations.job_sources.base import JobSourceAdapter, NormalizedJobPosting
from app.integrations.job_sources.custom_rss import CustomRSSAdapter
from app.integrations.job_sources.greenhouse import GreenhouseAdapter
from app.integrations.job_sources.lever import LeverAdapter
from app.integrations.job_sources.remoteok import RemoteOKAdapter
from app.integrations.job_sources.remotive import RemotiveAdapter
from app.integrations.job_sources.themuse import TheMuseAdapter
from app.integrations.job_sources.usajobs import USAJobsAdapter

ADAPTERS: dict[str, JobSourceAdapter] = {
    "adzuna": AdzunaAdapter(),
    "remotive": RemotiveAdapter(),
    "remoteok": RemoteOKAdapter(),
    "arbeitnow": ArbeitnowAdapter(),
    "usajobs": USAJobsAdapter(),
    "themuse": TheMuseAdapter(),
    "greenhouse": GreenhouseAdapter(),
    "lever": LeverAdapter(),
    "custom_rss": CustomRSSAdapter(),
}


def get_adapter(source_type: str) -> JobSourceAdapter | None:
    return ADAPTERS.get(source_type)


__all__ = ["ADAPTERS", "get_adapter", "NormalizedJobPosting"]
