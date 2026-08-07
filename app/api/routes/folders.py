from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_uow
from app.api.schemas.folders import CreateFolderRequest, FolderResponse
from app.application.folders_service import FolderService
from app.application.exceptions import NotFoundError
from app.domain.auth import AuthenticatedUser
from app.application.uow import SQLAlchemyUnitOfWork

router = APIRouter(prefix="/folders", tags=["folders"])


def get_folder_service(uow: SQLAlchemyUnitOfWork = Depends(get_uow)) -> FolderService:
    return FolderService(uow=uow)


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: CreateFolderRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    folder_service: FolderService = Depends(get_folder_service),
) -> FolderResponse:
    result = await folder_service.create_folder(owner=current_user, name=payload.name, parent_id=payload.parent_id)
    return FolderResponse(folder_id=result.folder_id, name=result.name, parent_id=result.parent_id)


@router.get("", response_model=list[FolderResponse])
async def list_folders(
    current_user: AuthenticatedUser = Depends(get_current_user),
    folder_service: FolderService = Depends(get_folder_service),
) -> list[FolderResponse]:
    folders = await folder_service.list_folders(owner=current_user)
    return [FolderResponse(folder_id=folder.id, name=folder.name, parent_id=folder.parent_id) for folder in folders]
