from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SearchTransferResponse(BaseModel):
    transfer_id: str
    transfer_code: str | None
    original_name: str
    size_bytes: int
    status: str
    expires_at: datetime | None
