from __future__ import annotations

import hashlib
import os
from pathlib import Path

import anyio

from app.domain.storage import FileStorage, StoredFile


class LocalFileStorage(FileStorage):
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path
        self._root_path.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, *, source_name: str, destination_name: str, content) -> StoredFile:
        destination_path = self._root_path / destination_name
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        sha256 = hashlib.sha256()
        size_bytes = 0

        def _write_file() -> StoredFile:
            nonlocal size_bytes
            with destination_path.open("wb") as target:
                while True:
                    chunk = content.file.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    sha256.update(chunk)
                    size_bytes += len(chunk)
            return StoredFile(path=destination_path, size_bytes=size_bytes, sha256=sha256.hexdigest())

        return await anyio.to_thread.run_sync(_write_file)

    async def delete(self, stored_file: StoredFile) -> None:
        if stored_file.path.exists():
            await anyio.to_thread.run_sync(stored_file.path.unlink)
