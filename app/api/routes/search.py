from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_uow
from app.api.schemas.search import SearchTransferResponse
from app.application.transfers_service import TransferService
from app.application.transfer_codes import TransferCodeGenerator
from app.application.uow import SQLAlchemyUnitOfWork
from app.core.settings import Settings, get_settings
from app.domain.auth import AuthenticatedUser
from app.infrastructure.storage.local import LocalFileStorage

router = APIRouter(prefix="/search", tags=["search"])


def get_transfer_service(settings: Settings = Depends(get_settings), uow: SQLAlchemyUnitOfWork = Depends(get_uow)) -> TransferService:
    return TransferService(uow=uow, file_storage=LocalFileStorage(settings.uploads_dir), code_generator=TransferCodeGenerator())


@router.get("/transfers", response_model=list[SearchTransferResponse])
async def search_transfers(
    q: str = Query(min_length=1, max_length=255),
    current_user: AuthenticatedUser = Depends(get_current_user),
    transfer_service: TransferService = Depends(get_transfer_service),
) -> list[SearchTransferResponse]:
    results = []
    matches = await transfer_service.search_transfers(owner_id=current_user.user_id, query=q)
    for transfer in matches:
        results.append(
            SearchTransferResponse(
                transfer_id=str(transfer.id),
                transfer_code=transfer.transfer_code,
                original_name=transfer.original_name,
                size_bytes=transfer.size_bytes,
                status=transfer.status.value,
                expires_at=transfer.expires_at,
            )
        )
    return results
