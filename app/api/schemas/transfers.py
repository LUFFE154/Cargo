from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TransferUploadResponse(BaseModel):
    transfer_id: str
    transfer_code: str = Field(min_length=6, max_length=6)
    download_url: str
    expires_at: datetime | None
    sha256: str
    size_bytes: int
    original_name: str


class TransferDownloadResponse(BaseModel):
    transfer_id: str
    transfer_code: str
    original_name: str
    size_bytes: int
    sha256: str | None
    status: str
    expires_at: datetime | None
