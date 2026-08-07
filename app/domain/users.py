from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True, kw_only=True)
class User:
    email: str
    password_hash: str
    display_name: str | None = None
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
