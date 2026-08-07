from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True, frozen=True)
class StoredFile:
    path: Path
    size_bytes: int
    sha256: str


class FileStorage(Protocol):
    async def save_upload(self, *, source_name: str, destination_name: str, content) -> StoredFile:
        ...

    async def delete(self, stored_file: StoredFile) -> None:
        ...
