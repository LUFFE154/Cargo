from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.uploads import UploadSession


class UploadSessionRepository(Protocol):
    async def create(self, session: UploadSession) -> UploadSession:
        ...

    async def get(self, session_id: UUID) -> UploadSession | None:
        ...

    async def save(self, session: UploadSession) -> UploadSession:
        ...

    async def delete(self, session_id: UUID) -> None:
        ...

    async def list_expired_before(self, deadline: datetime) -> list[UploadSession]:
        ...
