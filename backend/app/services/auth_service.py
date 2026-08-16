from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.profile import Profile
from app.models.user import User
from app.security import create_access_token, hash_password, verify_password

settings = get_settings()


class AuthError(Exception):
    pass


async def register_owner(db: AsyncSession, email: str, password: str) -> User:
    """Create the single owner account. Only permitted while `users` is
    empty and registration is enabled - this is a self-hosted, single/few
    -user tool, not a multi-tenant SaaS, so there is no open signup surface.
    """
    if not settings.allow_registration_if_empty:
        raise AuthError("Registration is disabled.")

    existing_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    if existing_count > 0:
        raise AuthError("An account already exists on this server. Registration is locked.")

    user = User(email=email.lower(), hashed_password=hash_password(password))
    db.add(user)
    await db.flush()

    # Every user gets an empty profile shell immediately so downstream
    # features (CV upload, matching) always have somewhere to write to.
    db.add(Profile(user_id=user.id, email=user.email))

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password.")
    if not user.is_active:
        raise AuthError("Account is disabled.")
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id)
