from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CreateFolderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: UUID | None = None


class FolderResponse(BaseModel):
    folder_id: UUID
    name: str
    parent_id: UUID | None
