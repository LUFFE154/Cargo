from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import FolderRepository
from app.domain.transfers import Folder
from app.infrastructure.db.mappers import folder_to_domain, folder_to_model
from app.infrastructure.db.models import FolderModel


class SQLAlchemyFolderRepository(FolderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, folder: Folder) -> Folder:
        model = folder_to_model(folder)
        self._session.add(model)
        await self._session.flush()
        return folder

    async def list_for_owner(self, owner_id: UUID) -> list[Folder]:
        result = await self._session.execute(
            select(FolderModel).where(FolderModel.owner_id == owner_id).order_by(FolderModel.created_at.asc())
        )
        return [folder_to_domain(model) for model in result.scalars().all()]
