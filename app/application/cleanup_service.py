from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.domain.repositories import UnitOfWork
from app.domain.storage import FileStorage, StoredFile


class CleanupService:
    def __init__(self, uow: UnitOfWork, file_storage: FileStorage) -> None:
        self._uow = uow
        self._file_storage = file_storage

    async def cleanup_expired_transfers(self, *, deadline: datetime | None = None) -> int:
        cutoff = deadline or datetime.now(UTC)
        async with self._uow as uow:
            expired_transfers = await uow.transfers.list_expired_before(cutoff)

            removed = 0
            for transfer in expired_transfers:
                if transfer.storage_path:
                    await self._file_storage.delete(
                        StoredFile(path=Path(transfer.storage_path), size_bytes=transfer.size_bytes, sha256=transfer.checksum_sha256 or "")
                    )
                await uow.transfers.delete_by_id(transfer.id)
                removed += 1

            await uow.commit()
            return removed
