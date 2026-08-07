from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateUploadSessionRequest(BaseModel):
    original_name: str = Field(min_length=1, max_length=255)
    total_size_bytes: int = Field(gt=0)
    folder_id: UUID | None = None
    expires_in_seconds: int | None = Field(default=None, gt=0)


class UploadSessionResponse(BaseModel):
    session_id: UUID
    status: str
    received_bytes: int
    total_size_bytes: int
    expires_at: datetime | None


class AppendChunkResponse(BaseModel):
    session_id: UUID
    status: str
    received_bytes: int
    total_size_bytes: int
    completed: bool
    transfer_code: str | None = None
    download_url: str | None = None
