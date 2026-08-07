from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.auth import AuthenticatedUser
from app.domain.transfers import Folder
from app.domain.repositories import UnitOfWork


@dataclass(slots=True)
class CreateFolderResult:
    folder_id: UUID
    name: str
    parent_id: UUID | None


class FolderService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create_folder(self, *, owner: AuthenticatedUser, name: str, parent_id: UUID | None = None) -> CreateFolderResult:
        folder = Folder(owner_id=owner.user_id, name=name, parent_id=parent_id)
        async with self._uow as uow:
            await uow.folders.add(folder)
            await uow.commit()
        return CreateFolderResult(folder_id=folder.id, name=folder.name, parent_id=folder.parent_id)

    async def list_folders(self, *, owner: AuthenticatedUser) -> list[Folder]:
        async with self._uow as uow:
            return list(await uow.folders.list_for_owner(owner.user_id))
