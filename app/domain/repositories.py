from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence
from uuid import UUID

from app.domain.transfers import Folder, Transfer
from app.domain.upload_sessions import UploadSessionRepository


class TransferRepository(Protocol):
    async def add(self, transfer: Transfer) -> Transfer:
        ...

    async def save(self, transfer: Transfer) -> Transfer:
        ...

    async def delete_by_id(self, transfer_id: UUID) -> None:
        ...

    async def get_by_id(self, transfer_id: UUID) -> Transfer | None:
        ...

    async def get_by_code(self, transfer_code: str) -> Transfer | None:
        ...

    async def list_for_owner(self, owner_id: UUID, limit: int = 50) -> Sequence[Transfer]:
        ...

    async def search(self, owner_id: UUID, query: str, limit: int = 20) -> Sequence[Transfer]:
        ...

    async def list_expired_before(self, deadline: datetime) -> Sequence[Transfer]:
        ...

    async def expire_before(self, deadline: datetime) -> int:
        ...


class FolderRepository(Protocol):
    async def add(self, folder: Folder) -> Folder:
        ...

    async def list_for_owner(self, owner_id: UUID) -> Sequence[Folder]:
        ...


class UnitOfWork(Protocol):
    transfers: TransferRepository
    folders: FolderRepository
    upload_sessions: UploadSessionRepository

    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...
