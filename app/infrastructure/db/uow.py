from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.uow import SQLAlchemyUnitOfWork


def build_uow(session_factory: async_sessionmaker[AsyncSession]) -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(session_factory)
