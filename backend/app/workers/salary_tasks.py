"""RQ task behind the nightly salary refresh cron (see workers/scheduler.py).
Precomputes snapshots for a curated set of common tech role/location pairs
so the Market page loads instantly for the common case; arbitrary queries
still get a live aggregated-postings computation at read time (see
services/salary_service.get_salary_insights).
"""
import asyncio

import structlog

from app.database import get_sync_session
from app.integrations.salary_apis.adzuna_salary import fetch_adzuna_salary_estimate
from app.integrations.salary_apis.bls import fetch_bls_wage_estimate
from app.services.salary_service import (
    COMMON_LOCATIONS,
    COMMON_ROLES,
    compute_aggregated_sync,
    upsert_snapshot_sync,
)

log = structlog.get_logger()


def refresh_all_salary_snapshots() -> None:
    with get_sync_session() as db:
        for role in COMMON_ROLES:
            for location in COMMON_LOCATIONS:
                aggregated = compute_aggregated_sync(db, role, location)
                if aggregated is not None:
                    upsert_snapshot_sync(db, role, location, "aggregated_postings", aggregated)

                adzuna = asyncio.run(fetch_adzuna_salary_estimate(role, location))
                if adzuna is not None:
                    upsert_snapshot_sync(db, role, location, "adzuna", adzuna)

                bls = asyncio.run(fetch_bls_wage_estimate(role))
                if bls is not None:
                    upsert_snapshot_sync(db, role, location, "bls", bls)

        log.info("salary.refresh_complete", roles=len(COMMON_ROLES), locations=len(COMMON_LOCATIONS))
