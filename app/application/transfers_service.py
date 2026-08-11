from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID
from typing import Sequence

from app.application.exceptions import NotFoundError
from app.application.transfer_codes import TransferCodeGenerator
from app.domain.auth import AuthenticatedUser
from app.domain.repositories import UnitOfWork
from app.domain.storage import FileStorage
from app.domain.transfers import Transfer, TransferStatus



DEFAULT_UPLOAD_NAME = "upload.bin"


@dataclass(slots=True)
class UploadTransferResult:
    transfer_id: UUID
    transfer_code: str
    download_url: str
    expires_at: datetime | None
    sha256: str
    size_bytes: int
    original_name: str


class TransferService:
    def __init__(self, uow: UnitOfWork, file_storage: FileStorage, code_generator: TransferCodeGenerator) -> None:
        self._uow = uow
        self._file_storage = file_storage
        self._code_generator = code_generator

    async def upload_file(
        self,
        *,
        owner: AuthenticatedUser,
        uploaded_file,
        expires_in_seconds: int | None,
        folder_id: UUID | None = None,
    ) -> UploadTransferResult:
        original_name = uploaded_file.filename or DEFAULT_UPLOAD_NAME
        stored_name = self._build_stored_name(owner.user_id, original_name)
        stored_file = await self._file_storage.save_upload(
            source_name=original_name,
            destination_name=stored_name,
            content=uploaded_file,
        )

        transfer = Transfer(
            owner_id=owner.user_id,
            folder_id=folder_id,
            original_name=original_name,
            stored_name=stored_name,
            storage_path=str(stored_file.path),
            size_bytes=stored_file.size_bytes,
            checksum_sha256=stored_file.sha256,
            status=TransferStatus.PROCESSING,
            search_text=original_name.lower(),
            sha256_verified=True,
        )

        async with self._uow as uow:
            code = await self._create_unique_transfer_code(uow, owner.user_id)
            transfer.mark_ready(
                transfer_code=code,
                expires_at=self._build_expiry(expires_in_seconds),
            )
            transfer.set_checksum(stored_file.sha256)
            transfer.storage_path = str(stored_file.path)
            await uow.transfers.add(transfer)
            await uow.commit()

        return UploadTransferResult(
            transfer_id=transfer.id,
            transfer_code=transfer.transfer_code or "",
            download_url=f"/api/v1/transfers/{transfer.transfer_code}/download",
            expires_at=transfer.expires_at,
            sha256=transfer.checksum_sha256 or stored_file.sha256,
            size_bytes=transfer.size_bytes,
            original_name=transfer.original_name,
        )

    async def register_completed_file(
        self,
        *,
        owner: AuthenticatedUser,
        original_name: str,
        stored_path: Path,
        size_bytes: int,
        checksum_sha256: str,
        expires_in_seconds: int | None,
        folder_id: UUID | None = None,
    ) -> UploadTransferResult:
        stored_name = self._build_stored_name(owner.user_id, original_name)
        transfer = Transfer(
            owner_id=owner.user_id,
            folder_id=folder_id,
            original_name=original_name,
            stored_name=stored_name,
            storage_path=str(stored_path),
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            status=TransferStatus.PROCESSING,
            search_text=original_name.lower(),
            sha256_verified=True,
        )

        async with self._uow as uow:
            code = await self._create_unique_transfer_code(uow, owner.user_id)
            transfer.mark_ready(transfer_code=code, expires_at=self._build_expiry(expires_in_seconds))
            transfer.set_checksum(checksum_sha256)
            await uow.transfers.add(transfer)
            await uow.commit()

        return UploadTransferResult(
            transfer_id=transfer.id,
            transfer_code=transfer.transfer_code or "",
            download_url=f"/api/v1/transfers/{transfer.transfer_code}/download",
            expires_at=transfer.expires_at,
            sha256=transfer.checksum_sha256 or checksum_sha256,
            size_bytes=transfer.size_bytes,
            original_name=transfer.original_name,
        )

    async def resolve_transfer(self, transfer_code: str) -> Transfer:
        async with self._uow as uow:
            transfer = await uow.transfers.get_by_code(transfer_code)

        if transfer is None:
            raise NotFoundError("Transfer not found")
        return transfer

    async def mark_downloaded(self, transfer_code: str) -> Transfer:
        async with self._uow as uow:
            transfer = await uow.transfers.get_by_code(transfer_code)
            if transfer is None:
                raise NotFoundError("Transfer not found")

            transfer.mark_downloaded()
            await uow.transfers.save(transfer)
            await uow.commit()
            return transfer

    async def search_transfers(
        self,
        *,
        owner_id: UUID,
        query: str,
    ) -> list[Transfer]:
        async with self._uow as uow:
            return list(await uow.transfers.search(owner_id, query))

    async def list_for_owner(
        self,
        owner_id: UUID,
        limit: int = 50,
    ) -> Sequence[Transfer]:
        async with self._uow as uow:
            return await uow.transfers.list_for_owner(owner_id, limit)

    async def _create_unique_transfer_code(
        self,
        uow: UnitOfWork,
        owner_id: UUID,
    ) -> str:
        for _ in range(20):
            code = self._code_generator.generate()
            existing = await uow.transfers.get_by_code(code)

            if existing is None or existing.owner_id == owner_id:
                return code

        raise RuntimeError("Unable to generate a unique transfer code")

    def _build_expiry(
        self,
        expires_in_seconds: int | None,
    ) -> datetime | None:
        if expires_in_seconds is None:
            return None

        return datetime.now(UTC) + timedelta(
            seconds=expires_in_seconds
        )

    def _build_stored_name(
        self,
        owner_id: UUID,
        original_name: str,
    ) -> str:
        safe_name = original_name.replace(" ", "_")
        return f"{owner_id}_{safe_name}"

