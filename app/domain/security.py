from __future__ import annotations

from typing import Protocol

from app.domain.auth import AuthenticatedUser
from app.domain.users import User


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str:
        ...

    def verify_password(self, password: str, password_hash: str) -> bool:
        ...


class TokenService(Protocol):
    def create_access_token(self, user: AuthenticatedUser) -> str:
        ...

    def parse_access_token(self, token: str) -> AuthenticatedUser:
        ...


class UserRepository(Protocol):
    async def add(self, user: User) -> User:
        ...

    async def get_by_id(self, user_id) -> User | None:
        ...

    async def get_by_email(self, email: str) -> User | None:
        ...
