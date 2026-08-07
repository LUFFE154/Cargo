from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class AuthenticatedUser:
    user_id: UUID
    email: str
    is_admin: bool = False
