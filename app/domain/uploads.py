from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4


class UploadSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, kw_only=True)
class UploadSession:
    owner_id: UUID
    original_name: str
    total_size_bytes: int
    temp_path: Path
    id: UUID = field(default_factory=uuid4)
    folder_id: UUID | None = None
    received_bytes: int = 0
    status: UploadSessionStatus = UploadSessionStatus.ACTIVE
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def advance(self, bytes_written: int) -> None:
        self.received_bytes += bytes_written
        self.updated_at = _utcnow()

    def mark_completed(self) -> None:
        self.status = UploadSessionStatus.COMPLETED
        self.updated_at = _utcnow()
