from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    resolved_database_url = database_url or settings.database_url
    return create_async_engine(resolved_database_url, echo=False, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory(database_url: str | None = None) -> async_sessionmaker[AsyncSession]:
    engine = get_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


def session_factory_from_settings(settings: Settings) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(settings.database_url), expire_on_commit=False, autoflush=False)
