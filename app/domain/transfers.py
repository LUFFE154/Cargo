from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class TransferStatus(StrEnum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    DOWNLOADED = "downloaded"
    EXPIRED = "expired"
    FAILED = "failed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, kw_only=True)
class Transfer:
    owner_id: UUID
    original_name: str
    stored_name: str
    size_bytes: int
    id: UUID = field(default_factory=uuid4)
    checksum_sha256: str | None = None
    transfer_code: str | None = None
    status: TransferStatus = TransferStatus.UPLOADING
    expires_at: datetime | None = None
    downloaded_at: datetime | None = None
    folder_id: UUID | None = None
    version_number: int = 1
    storage_path: str | None = None
    search_text: str = ""
    sha256_verified: bool = False
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def mark_processing(self) -> None:
        self.status = TransferStatus.PROCESSING
        self.updated_at = _utcnow()

    def mark_ready(self, transfer_code: str, expires_at: datetime | None) -> None:
        self.transfer_code = transfer_code
        self.expires_at = expires_at
        self.status = TransferStatus.READY
        self.updated_at = _utcnow()

    def mark_downloaded(self) -> None:
        self.status = TransferStatus.DOWNLOADED
        self.downloaded_at = _utcnow()
        self.updated_at = _utcnow()

    def mark_expired(self) -> None:
        self.status = TransferStatus.EXPIRED
        self.updated_at = _utcnow()

    def set_checksum(self, checksum_sha256: str) -> None:
        self.checksum_sha256 = checksum_sha256
        self.sha256_verified = True
        self.updated_at = _utcnow()


@dataclass(slots=True, kw_only=True)
class Folder:
    owner_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    parent_id: UUID | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
