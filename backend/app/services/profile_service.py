from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import (
    Certification,
    Education,
    Language,
    Profile,
    Project,
    Skill,
    WorkExperience,
)
from app.models.user import User
from app.schemas.profile import ProfileIn


def _eager_options():
    return (
        selectinload(Profile.work_experience),
        selectinload(Profile.education),
        selectinload(Profile.certifications),
        selectinload(Profile.projects),
        selectinload(Profile.languages),
        selectinload(Profile.skills),
    )


async def get_or_create_profile(db: AsyncSession, user: User) -> Profile:
    stmt = select(Profile).where(Profile.user_id == user.id).options(*_eager_options())
    profile = (await db.execute(stmt)).scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id, email=user.email)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        profile = (await db.execute(stmt)).scalar_one()
    return profile


async def replace_profile(db: AsyncSession, user: User, payload: ProfileIn) -> Profile:
    """Full-form save: the CV builder submits the entire profile at once
    (matches the React Hook Form useFieldArray UX), so the simplest correct
    approach is to overwrite scalar fields and fully resync each child
    collection from the submitted list, preserving submitted order via
    order_index. This is simpler and less error-prone than diffing
    individual list items across requests.
    """
    profile = await get_or_create_profile(db, user)

    profile.full_name = payload.full_name
    profile.headline = payload.headline
    profile.summary = payload.summary
    profile.location = payload.location
    profile.phone = payload.phone
    profile.email = payload.email or user.email
    profile.links = payload.links.model_dump()

    profile.work_experience.clear()
    for i, item in enumerate(payload.work_experience):
        profile.work_experience.append(WorkExperience(**item.model_dump(), order_index=i))

    profile.education.clear()
    for i, item in enumerate(payload.education):
        profile.education.append(Education(**item.model_dump(), order_index=i))

    profile.certifications.clear()
    for i, item in enumerate(payload.certifications):
        profile.certifications.append(Certification(**item.model_dump(), order_index=i))

    profile.projects.clear()
    for i, item in enumerate(payload.projects):
        profile.projects.append(Project(**item.model_dump(), order_index=i))

    profile.languages.clear()
    for i, item in enumerate(payload.languages):
        profile.languages.append(Language(**item.model_dump(), order_index=i))

    profile.skills.clear()
    for i, item in enumerate(payload.skills):
        profile.skills.append(Skill(**item.model_dump(), order_index=i))

    # Embedding is now stale; matching_service regenerates it out-of-band.
    profile.embedding = None

    await db.commit()

    stmt = select(Profile).where(Profile.id == profile.id).options(*_eager_options())
    return (await db.execute(stmt)).scalar_one()
