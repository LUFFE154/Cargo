from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.repositories import FolderRepository, TransferRepository, UnitOfWork
from app.infrastructure.cache.redis_upload_sessions import RedisUploadSessionRepository
from app.infrastructure.repositories.folders import SQLAlchemyFolderRepository
from app.infrastructure.repositories.transfers import SQLAlchemyTransferRepository
from app.infrastructure.repositories.users import SQLAlchemyUserRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], redis_url: str) -> None:
        self._session_factory = session_factory
        self._redis_url = redis_url
        self.session: AsyncSession | None = None
        self.transfers: TransferRepository
        self.folders: FolderRepository
        self.users: SQLAlchemyUserRepository
        self.upload_sessions: RedisUploadSessionRepository
        self.redis: Redis | None = None

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.redis = Redis.from_url(self._redis_url, decode_responses=True)
        self.transfers = SQLAlchemyTransferRepository(self.session)
        self.folders = SQLAlchemyFolderRepository(self.session)
        self.users = SQLAlchemyUserRepository(self.session)
        self.upload_sessions = RedisUploadSessionRepository(self.redis)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.session is None:
            return
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()
        if self.redis is not None:
            await self.redis.aclose()
        self.session = None
        self.redis = None

    async def commit(self) -> None:
        if self.session is not None:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session is not None:
            await self.session.rollback()
