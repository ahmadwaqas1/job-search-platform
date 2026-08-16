"""Import every model module here so SQLAlchemy's mapper registry sees all
classes (needed for relationship() string resolution and for Alembic
autogenerate to see the full schema via Base.metadata).
"""
from app.models.app_settings import AppSetting  # noqa: F401
from app.models.application import Application, ApplicationEvent  # noqa: F401
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.cv import CVDocument  # noqa: F401
from app.models.job import JobPosting, JobSource  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.profile import (  # noqa: F401
    Certification,
    Education,
    Language,
    Profile,
    Project,
    Skill,
    WorkExperience,
)
from app.models.salary import SalarySnapshot  # noqa: F401
from app.models.user import User  # noqa: F401
