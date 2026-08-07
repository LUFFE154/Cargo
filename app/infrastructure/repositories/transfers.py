from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import TransferRepository
from app.domain.transfers import Transfer
from app.infrastructure.db.mappers import transfer_to_domain, transfer_to_model
from app.infrastructure.db.models import TransferModel


class SQLAlchemyTransferRepository(TransferRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transfer: Transfer) -> Transfer:
        model = transfer_to_model(transfer)
        self._session.add(model)
        await self._session.flush()
        return transfer

    async def save(self, transfer: Transfer) -> Transfer:
        await self._session.merge(transfer_to_model(transfer))
        await self._session.flush()
        return transfer

    async def delete_by_id(self, transfer_id: UUID) -> None:
        await self._session.execute(delete(TransferModel).where(TransferModel.id == transfer_id))
        await self._session.flush()

    async def get_by_id(self, transfer_id: UUID) -> Transfer | None:
        result = await self._session.execute(select(TransferModel).where(TransferModel.id == transfer_id))
        model = result.scalar_one_or_none()
        return transfer_to_domain(model) if model is not None else None

    async def get_by_code(self, transfer_code: str) -> Transfer | None:
        result = await self._session.execute(select(TransferModel).where(TransferModel.transfer_code == transfer_code))
        model = result.scalar_one_or_none()
        return transfer_to_domain(model) if model is not None else None

    async def list_for_owner(self, owner_id: UUID, limit: int = 50) -> list[Transfer]:
        result = await self._session.execute(
            select(TransferModel)
            .where(TransferModel.owner_id == owner_id)
            .order_by(TransferModel.created_at.desc())
            .limit(limit)
        )
        return [transfer_to_domain(model) for model in result.scalars().all()]

    async def search(self, owner_id: UUID, query: str, limit: int = 20) -> list[Transfer]:
        like_query = f"%{query}%"
        result = await self._session.execute(
            select(TransferModel)
            .where(TransferModel.owner_id == owner_id)
            .where(
                (TransferModel.original_name.ilike(like_query))
                | (TransferModel.search_text.ilike(like_query))
            )
            .order_by(TransferModel.created_at.desc())
            .limit(limit)
        )
        return [transfer_to_domain(model) for model in result.scalars().all()]

    async def list_expired_before(self, deadline: datetime) -> list[Transfer]:
        result = await self._session.execute(
            select(TransferModel)
            .where(TransferModel.expires_at.is_not(None))
            .where(TransferModel.expires_at <= deadline)
            .order_by(TransferModel.expires_at.asc())
        )
        return [transfer_to_domain(model) for model in result.scalars().all()]

    async def expire_before(self, deadline: datetime) -> int:
        result = await self._session.execute(
            delete(TransferModel).where(TransferModel.expires_at.is_not(None)).where(TransferModel.expires_at <= deadline)
        )
        return int(result.rowcount or 0)
