from __future__ import annotations

import hashlib
import shutil
import uuid
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
    def __init__(
        self,
        uow: UnitOfWork,
        transfer_service: TransferService,
        uploads_root: Path,
        temp_root: Path,
    ) -> None:
        self._uow = uow
        self._transfer_service = transfer_service
        self._uploads_root = uploads_root
        self._temp_root = temp_root
        self._temp_root.mkdir(parents=True, exist_ok=True)
        self._uploads_root.mkdir(parents=True, exist_ok=True)

        self._session_locks: dict[UUID, anyio.Lock] = {}
        self._locks_guard = anyio.Lock()

        # In-memory incremental checksum state keyed by session ID.
        # This avoids re‑reading the entire file at the end of the upload.
        self._checksums: dict[UUID, hashlib._Hash] = {}
        self._checksums_guard = anyio.Lock()

    async def create_session(
        self,
        *,
        owner: AuthenticatedUser,
        original_name: str,
        total_size_bytes: int,
        expires_in_seconds: int | None,
        folder_id: UUID | None = None,
    ) -> UploadSessionResult:
        safe_name = self._safe_basename(original_name)
        temp_path = self._temp_root / f"{owner.user_id}_{uuid.uuid4().hex}.part"

        session = UploadSession(
            owner_id=owner.user_id,
            folder_id=folder_id,
            original_name=safe_name,
            total_size_bytes=total_size_bytes,
            temp_path=temp_path,
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

    async def append_chunk(
        self,
        *,
        owner: AuthenticatedUser,
        session_id: UUID,
        upload_offset: int,
        chunk_size: int,
        chunk,
    ) -> ChunkUploadResult:
        lock = await self._get_session_lock(session_id)
        async with lock:
            async with self._uow as uow:
                session = await uow.upload_sessions.get(session_id)

            if session is None:
                raise NotFoundError("Upload session not found")
            if session.owner_id != owner.user_id:
                raise NotFoundError("Upload session not found")
            if session.status != UploadSessionStatus.ACTIVE:
                raise NotFoundError("Upload session is no longer active")
            if session.expires_at is not None and datetime.now(UTC) >= session.expires_at:
                raise NotFoundError("Upload session has expired")

            # --- Offset validation ---
            if upload_offset != session.received_bytes:
                raise ValueError("Invalid upload offset")

            # --- Size validation ---
            remaining_bytes = session.total_size_bytes - session.received_bytes
            if chunk_size <= 0:
                raise ValueError("Chunk size must be positive")
            if chunk_size > remaining_bytes:
                raise ValueError("Chunk exceeds remaining upload size")

            # Get the running hash (creates or rebuilds if needed)
            hasher = await self._get_checksum(session.id, session.temp_path)

            # Stream the chunk to disk while updating the hash.
            # No rollback needed because size and offset are pre‑validated.
            bytes_written = await self._append_to_temp_file(
                temp_path=session.temp_path,
                chunk=chunk,
                chunk_size=chunk_size,
                hasher=hasher,
            )
            session.advance(bytes_written)

            if session.received_bytes >= session.total_size_bytes:
                session.mark_completed()
                final_path = await self._finalize_temp_file(
                    session.temp_path, session.original_name
                )

                checksum = hasher.hexdigest()

                try:
                    result = await self._transfer_service.register_completed_file(
                        owner=owner,
                        original_name=session.original_name,
                        stored_path=final_path,
                        size_bytes=session.received_bytes,
                        checksum_sha256=checksum,
                        expires_in_seconds=(
                            None
                            if session.expires_at is None
                            else int(
                                (session.expires_at - datetime.now(UTC)).total_seconds()
                            )
                        ),
                        folder_id=session.folder_id,
                    )
                except Exception:
                    await anyio.to_thread.run_sync(
                        lambda: final_path.unlink(missing_ok=True)
                    )
                    raise
                finally:
                    # Always remove the in‑memory checksum entry,
                    # even if registration fails.
                    await self._remove_checksum(session.id)

                # If registration succeeded, delete the session record.
                # If deletion fails, the checksum is already cleaned up.
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

            # Save the updated session state (not completed)
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

    # ------------------------------------------------------------------ #
    # Checksum helpers
    # ------------------------------------------------------------------ #
    async def _get_checksum(
        self, session_id: UUID, temp_path: Path
    ) -> hashlib._Hash:
        """
        Return the running hash object for the session, creating it if necessary.
        If the in‑memory state is missing (e.g. after restart), rebuild from disk once.
        """
        async with self._checksums_guard:
            hasher = self._checksums.get(session_id)
            if hasher is not None:
                return hasher

            new_hasher = hashlib.sha256()
            if temp_path.exists():
                def update_from_file() -> None:
                    with temp_path.open("rb") as f:
                        while True:
                            block = f.read(16 * 1024 * 1024)
                            if not block:
                                break
                            new_hasher.update(block)

                await anyio.to_thread.run_sync(update_from_file)

            self._checksums[session_id] = new_hasher
            return new_hasher

    async def _remove_checksum(self, session_id: UUID) -> None:
        async with self._checksums_guard:
            self._checksums.pop(session_id, None)

    # ------------------------------------------------------------------ #
    # File I/O – all blocking operations run in a worker thread
    # ------------------------------------------------------------------ #
    async def _append_to_temp_file(
        self,
        *,
        temp_path: Path,
        chunk,
        chunk_size: int,
        hasher: hashlib._Hash,
    ) -> int:
        """
        Stream exactly `chunk_size` bytes from the chunk to the temp file,
        updating the hash in place. Runs in a worker thread.
        """
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        def _sync_append() -> int:
            written = 0
            with temp_path.open("ab") as target:
                while written < chunk_size:
                    read_size = min(16 * 1024 * 1024, chunk_size - written)
                    data = chunk.file.read(read_size)
                    if not data:
                        raise ValueError("Unexpected end of chunk")

                    target.write(data)
                    hasher.update(data)
                    written += len(data)

            return written

        return await anyio.to_thread.run_sync(_sync_append)

    async def _finalize_temp_file(
        self, temp_path: Path, original_name: str
    ) -> Path:
        final_name = f"{uuid.uuid4().hex}_{original_name}"
        final_path = self._uploads_root / final_name
        await anyio.to_thread.run_sync(shutil.move, str(temp_path), str(final_path))
        return final_path

    def _safe_basename(self, original_name: str) -> str:
        name = original_name.replace("\\", "/").rsplit("/", 1)[-1]
        if not name or name in {".", ".."}:
            raise ValueError("Invalid original filename")
        return name.replace(" ", "_")

    def _build_expiry(self, expires_in_seconds: int | None) -> datetime | None:
        if expires_in_seconds is None:
            return None
        return datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

    # ------------------------------------------------------------------ #
    # Lock helpers
    # ------------------------------------------------------------------ #
    async def _get_session_lock(self, session_id: UUID) -> anyio.Lock:
        async with self._locks_guard:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = anyio.Lock()
                self._session_locks[session_id] = lock
            return lock