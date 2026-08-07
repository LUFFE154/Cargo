from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.security import UserRepository
from app.domain.users import User
from app.infrastructure.db.models import UserModel


def _user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        display_name=model.display_name,
        is_active=model.is_active,
        is_admin=model.is_admin,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _user_to_model(domain: User) -> UserModel:
    return UserModel(
        id=domain.id,
        email=domain.email,
        password_hash=domain.password_hash,
        display_name=domain.display_name,
        is_active=domain.is_active,
        is_admin=domain.is_admin,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        model = _user_to_model(user)
        self._session.add(model)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return _user_to_domain(model) if model is not None else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return _user_to_domain(model) if model is not None else None
