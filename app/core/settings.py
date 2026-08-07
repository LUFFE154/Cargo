from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def _csv_to_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = "Cargo"
    environment: Literal["development", "staging", "production", "test"] = "development"
    api_prefix: str = "/api/v1"
    data_dir: Path = Path("./data")
    uploads_dir: Path = Path("./data/uploads")
    temp_dir: Path = Path("./data/tmp")
    database_url: str = "postgresql+psycopg://cargo:cargo@localhost:5432/cargo"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    transfer_code_ttl_seconds: int = 900
    cleanup_interval_seconds: int = 300
    max_upload_size_mb: int = 10240
    allowed_origins: list[str] = Field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("CARGO_APP_NAME", "Cargo"),
            environment=os.getenv("CARGO_ENVIRONMENT", "development"),
            api_prefix=os.getenv("CARGO_API_PREFIX", "/api/v1"),
            data_dir=Path(os.getenv("CARGO_DATA_DIR", "./data")),
            uploads_dir=Path(os.getenv("CARGO_UPLOADS_DIR", "./data/uploads")),
            temp_dir=Path(os.getenv("CARGO_TEMP_DIR", "./data/tmp")),
            database_url=os.getenv(
                "CARGO_DATABASE_URL",
                "postgresql+psycopg://cargo:cargo@localhost:5432/cargo",
            ),
            redis_url=os.getenv("CARGO_REDIS_URL", "redis://localhost:6379/0"),
            log_level=os.getenv("CARGO_LOG_LEVEL", "INFO"),
            transfer_code_ttl_seconds=int(os.getenv("CARGO_TRANSFER_CODE_TTL_SECONDS", "900")),
            cleanup_interval_seconds=int(os.getenv("CARGO_CLEANUP_INTERVAL_SECONDS", "300")),
            max_upload_size_mb=int(os.getenv("CARGO_MAX_UPLOAD_SIZE_MB", "10240")),
            allowed_origins=_csv_to_list(os.getenv("CARGO_ALLOWED_ORIGINS")),
        )

    def ensure_storage_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
