from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from redis.asyncio import Redis

from app.domain.upload_sessions import UploadSessionRepository
from app.domain.uploads import UploadSession, UploadSessionStatus


class RedisUploadSessionRepository(UploadSessionRepository):
    def __init__(self, client: Redis) -> None:
        self._client = client

    def _key(self, session_id: UUID) -> str:
        return f"cargo:upload-session:{session_id}"

    async def create(self, session: UploadSession) -> UploadSession:
        await self.save(session)
        return session

    async def get(self, session_id: UUID) -> UploadSession | None:
        raw = await self._client.get(self._key(session_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return UploadSession(
            id=UUID(data["id"]),
            owner_id=UUID(data["owner_id"]),
            folder_id=UUID(data["folder_id"]) if data.get("folder_id") else None,
            original_name=data["original_name"],
            total_size_bytes=int(data["total_size_bytes"]),
            temp_path=Path(data["temp_path"]),
            received_bytes=int(data["received_bytes"]),
            status=UploadSessionStatus(data["status"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    async def save(self, session: UploadSession) -> UploadSession:
        payload = {
            "id": str(session.id),
            "owner_id": str(session.owner_id),
            "folder_id": str(session.folder_id) if session.folder_id else None,
            "original_name": session.original_name,
            "total_size_bytes": session.total_size_bytes,
            "temp_path": str(session.temp_path),
            "received_bytes": session.received_bytes,
            "status": session.status.value,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        ttl_seconds = None
        if session.expires_at is not None:
            ttl_seconds = max(1, int((session.expires_at - datetime.now(UTC)).total_seconds()))
        await self._client.set(self._key(session.id), json.dumps(payload), ex=ttl_seconds)
        return session

    async def delete(self, session_id: UUID) -> None:
        await self._client.delete(self._key(session_id))

    async def list_expired_before(self, deadline: datetime) -> list[UploadSession]:
        return []
