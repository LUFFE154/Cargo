from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.domain.auth import AuthenticatedUser
from app.domain.security import PasswordHasher, TokenService
from app.domain.users import User
from app.domain.repositories import UnitOfWork


@dataclass(slots=True)
class AuthResult:
    access_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher, token_service: TokenService) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> AuthResult:
        async with self._uow as uow:
            existing = await uow.users.get_by_email(email)
            if existing is not None:
                raise ConflictError("A user with this email already exists")

            user = User(
                email=email,
                password_hash=self._password_hasher.hash_password(password),
                display_name=display_name,
            )
            await uow.users.add(user)
            await uow.commit()

        return AuthResult(access_token=self._token_service.create_access_token(self._to_auth_user(user)))

    async def login(self, *, email: str, password: str) -> AuthResult:
        async with self._uow as uow:
            user = await uow.users.get_by_email(email)

        if user is None or not self._password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        return AuthResult(access_token=self._token_service.create_access_token(self._to_auth_user(user)))

    def get_current_user(self, token: str) -> AuthenticatedUser:
        try:
            return self._token_service.parse_access_token(token)
        except ValueError as exc:
            raise AuthenticationError(str(exc)) from exc

    async def require_user(self, user_id: UUID) -> User:
        async with self._uow as uow:
            user = await uow.users.get_by_id(user_id)

        if user is None:
            raise NotFoundError("User not found")
        return user

    def _to_auth_user(self, user: User) -> AuthenticatedUser:
        return AuthenticatedUser(user_id=user.id, email=user.email, is_admin=user.is_admin)
