from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create and cache the SQLAlchemy engine.

    Uses the configured `DATABASE_URL`. Failures should surface explicitly
    to callers.
    """

    settings: Settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_sessionmaker() -> sessionmaker[Session]:
    """Return a configured sessionmaker."""

    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)

