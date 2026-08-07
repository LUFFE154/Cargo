from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import anyio

from app.application.exceptions import NotFoundError
from app.application.transfers_service import TransferService
from app.domain.auth import AuthenticatedUser
from app.domain.uploads import UploadSession, UploadSessionStatus
from app.domain.repositories import UnitOfWork


@dataclass(slots=True)
class UploadSessionResult:
    session_id: UUID
    status: str
    received_bytes: int
    total_size_bytes: int
    expires_at: datetime | None


@dataclass(slots=True)
class ChunkUploadResult:
    session_id: UUID
    status: str
    received_bytes: int
    total_size_bytes: int
    completed: bool
    transfer_code: str | None = None
    download_url: str | None = None


class ChunkedUploadService:
    def __init__(self, uow: UnitOfWork, transfer_service: TransferService, uploads_root: Path, temp_root: Path) -> None:
        self._uow = uow
        self._transfer_service = transfer_service
        self._uploads_root = uploads_root
        self._temp_root = temp_root
        self._temp_root.mkdir(parents=True, exist_ok=True)
        self._uploads_root.mkdir(parents=True, exist_ok=True)

    async def create_session(
        self,
        *,
        owner: AuthenticatedUser,
        original_name: str,
        total_size_bytes: int,
        expires_in_seconds: int | None,
        folder_id: UUID | None = None,
    ) -> UploadSessionResult:
        session = UploadSession(
            owner_id=owner.user_id,
            folder_id=folder_id,
            original_name=original_name,
            total_size_bytes=total_size_bytes,
            temp_path=self._temp_root / f"{owner.user_id}_{original_name}.part",
            expires_at=self._build_expiry(expires_in_seconds),
        )
        async with self._uow as uow:
            await uow.upload_sessions.create(session)
            await uow.commit()

        return UploadSessionResult(
            session_id=session.id,
            status=session.status.value,
            received_bytes=session.received_bytes,
            total_size_bytes=session.total_size_bytes,
            expires_at=session.expires_at,
        )

    async def append_chunk(self, *, owner: AuthenticatedUser, session_id: UUID, chunk) -> ChunkUploadResult:
        async with self._uow as uow:
            session = await uow.upload_sessions.get(session_id)

        if session is None:
            raise NotFoundError("Upload session not found")
        if session.owner_id != owner.user_id:
            raise NotFoundError("Upload session not found")
        if session.status != UploadSessionStatus.ACTIVE:
            raise NotFoundError("Upload session is no longer active")

        bytes_written = await self._append_to_temp_file(session.temp_path, chunk)
        session.advance(bytes_written)

        if session.received_bytes >= session.total_size_bytes:
            session.mark_completed()
            final_path = await self._finalize_temp_file(session.temp_path, session.original_name)
            checksum = await self._checksum(final_path)
            result = await self._transfer_service.register_completed_file(
                owner=owner,
                original_name=session.original_name,
                stored_path=final_path,
                size_bytes=session.received_bytes,
                checksum_sha256=checksum,
                expires_in_seconds=None if session.expires_at is None else int((session.expires_at - datetime.now(UTC)).total_seconds()),
                folder_id=session.folder_id,
            )
            async with self._uow as uow:
                await uow.upload_sessions.delete(session.id)
                await uow.commit()
            return ChunkUploadResult(
                session_id=session.id,
                status=session.status.value,
                received_bytes=session.received_bytes,
                total_size_bytes=session.total_size_bytes,
                completed=True,
                transfer_code=result.transfer_code,
                download_url=result.download_url,
            )

        async with self._uow as uow:
            await uow.upload_sessions.save(session)
            await uow.commit()

        return ChunkUploadResult(
            session_id=session.id,
            status=session.status.value,
            received_bytes=session.received_bytes,
            total_size_bytes=session.total_size_bytes,
            completed=False,
        )

    async def get_session(self, session_id: UUID) -> UploadSession | None:
        async with self._uow as uow:
            return await uow.upload_sessions.get(session_id)

    async def _append_to_temp_file(self, temp_path: Path, chunk) -> int:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        size_written = 0
        while True:
            data = await chunk.read(1024 * 1024)
            if not data:
                break
            await anyio.to_thread.run_sync(self._append_bytes, temp_path, data)
            size_written += len(data)
        return size_written

    async def _finalize_temp_file(self, temp_path: Path, original_name: str) -> Path:
        final_path = self._uploads_root / original_name.replace(" ", "_")
        await anyio.to_thread.run_sync(shutil.move, str(temp_path), str(final_path))
        return final_path

    async def _checksum(self, file_path: Path) -> str:
        return await anyio.to_thread.run_sync(self._checksum_sync, file_path)

    def _append_bytes(self, temp_path: Path, data: bytes) -> None:
        with temp_path.open("ab") as target:
            target.write(data)

    def _checksum_sync(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with file_path.open("rb") as source:
            while True:
                data = source.read(1024 * 1024)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    def _build_expiry(self, expires_in_seconds: int | None) -> datetime | None:
        if expires_in_seconds is None:
            return None
        return datetime.now(UTC) + timedelta(seconds=expires_in_seconds)
