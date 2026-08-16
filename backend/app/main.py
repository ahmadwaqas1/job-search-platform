from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.job import JobSource
from app.routers import applications, auth, chat, cv, health, jobs, matching, profile, salary, settings as settings_router
from app.services.job_ingestion_service import DEFAULT_SOURCES

log = structlog.get_logger()
app_settings = get_settings()


async def _seed_default_job_sources() -> None:
    async with AsyncSessionLocal() as db:
        count = (
            await db.execute(select(func.count()).select_from(JobSource).where(JobSource.user_id.is_(None)))
        ).scalar_one()
        if count > 0:
            return
        for src in DEFAULT_SOURCES:
            db.add(
                JobSource(
                    user_id=None,
                    type=src["type"],
                    name=src["name"],
                    config=src.get("config", {}),
                    poll_interval_minutes=app_settings.default_job_poll_interval_minutes,
                    is_active=True,
                )
            )
        await db.commit()
        log.info("startup.seeded_default_job_sources", count=len(DEFAULT_SOURCES))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await _seed_default_job_sources()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Job Search Copilot API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in (
        health.router,
        auth.router,
        profile.router,
        cv.router,
        jobs.router,
        matching.router,
        applications.router,
        salary.router,
        chat.router,
        settings_router.router,
    ):
        app.include_router(router, prefix="/api")

    return app


app = create_app()
