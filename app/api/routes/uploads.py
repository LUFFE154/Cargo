from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_current_user, get_uow, get_settings
from app.api.schemas.uploads import AppendChunkResponse, CreateUploadSessionRequest, UploadSessionResponse
from app.application.chunked_uploads_service import ChunkedUploadService
from app.application.exceptions import NotFoundError
from app.application.transfer_codes import TransferCodeGenerator
from app.application.transfers_service import TransferService
from app.application.uow import SQLAlchemyUnitOfWork
from app.core.settings import Settings
from app.domain.auth import AuthenticatedUser
from app.infrastructure.storage.local import LocalFileStorage

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_transfer_service(settings: Settings = Depends(get_settings), uow: SQLAlchemyUnitOfWork = Depends(get_uow)) -> TransferService:
    return TransferService(uow=uow, file_storage=LocalFileStorage(settings.uploads_dir), code_generator=TransferCodeGenerator())


def get_chunked_upload_service(
    settings: Settings = Depends(get_settings),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
) -> ChunkedUploadService:
    transfer_service = get_transfer_service(settings=settings, uow=uow)
    return ChunkedUploadService(uow=uow, transfer_service=transfer_service, uploads_root=settings.uploads_dir, temp_root=settings.temp_dir)


@router.post("/sessions", response_model=UploadSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_upload_session(
    payload: CreateUploadSessionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    upload_service: ChunkedUploadService = Depends(get_chunked_upload_service),
) -> UploadSessionResponse:
    result = await upload_service.create_session(
        owner=current_user,
        original_name=payload.original_name,
        total_size_bytes=payload.total_size_bytes,
        expires_in_seconds=payload.expires_in_seconds,
        folder_id=payload.folder_id,
    )
    return UploadSessionResponse(
        session_id=result.session_id,
        status=result.status,
        received_bytes=result.received_bytes,
        total_size_bytes=result.total_size_bytes,
        expires_at=result.expires_at,
    )


@router.get("/sessions/{session_id}", response_model=UploadSessionResponse)
async def get_upload_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    upload_service: ChunkedUploadService = Depends(get_chunked_upload_service),
) -> UploadSessionResponse:
    session = await upload_service.get_session(session_id)
    if session is None or session.owner_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    return UploadSessionResponse(
        session_id=session.id,
        status=session.status.value,
        received_bytes=session.received_bytes,
        total_size_bytes=session.total_size_bytes,
        expires_at=session.expires_at,
    )


@router.patch("/sessions/{session_id}", response_model=AppendChunkResponse)
async def append_upload_chunk(
    session_id: UUID,
    chunk: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    upload_service: ChunkedUploadService = Depends(get_chunked_upload_service),
) -> AppendChunkResponse:
    try:
        result = await upload_service.append_chunk(owner=current_user, session_id=session_id, chunk=chunk)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AppendChunkResponse(
        session_id=result.session_id,
        status=result.status,
        received_bytes=result.received_bytes,
        total_size_bytes=result.total_size_bytes,
        completed=result.completed,
        transfer_code=result.transfer_code,
        download_url=result.download_url,
    )
