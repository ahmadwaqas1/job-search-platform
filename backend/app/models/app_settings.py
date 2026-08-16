from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSetting(Base):
    """Runtime-editable key/value settings (default models, poll defaults),
    seeded from environment variables on first boot but editable afterwards
    from the Settings page without a redeploy. See app/services/settings_service.py.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
