from __future__ import annotations

from app.domain.transfers import Folder, Transfer, TransferStatus
from app.infrastructure.db.models import FolderModel, TransferModel


def transfer_to_domain(model: TransferModel) -> Transfer:
    return Transfer(
        id=model.id,
        owner_id=model.owner_id,
        folder_id=model.folder_id,
        original_name=model.original_name,
        stored_name=model.stored_name,
        storage_path=model.storage_path,
        size_bytes=model.size_bytes,
        checksum_sha256=model.checksum_sha256,
        transfer_code=model.transfer_code,
        status=TransferStatus(model.status),
        expires_at=model.expires_at,
        downloaded_at=model.downloaded_at,
        version_number=model.version_number,
        search_text=model.search_text,
        sha256_verified=model.sha256_verified,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def transfer_to_model(domain: Transfer) -> TransferModel:
    return TransferModel(
        id=domain.id,
        owner_id=domain.owner_id,
        folder_id=domain.folder_id,
        original_name=domain.original_name,
        stored_name=domain.stored_name,
        storage_path=domain.storage_path or "",
        size_bytes=domain.size_bytes,
        checksum_sha256=domain.checksum_sha256,
        transfer_code=domain.transfer_code,
        status=domain.status.value,
        expires_at=domain.expires_at,
        downloaded_at=domain.downloaded_at,
        version_number=domain.version_number,
        search_text=domain.search_text,
        sha256_verified=domain.sha256_verified,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def folder_to_domain(model: FolderModel) -> Folder:
    return Folder(
        id=model.id,
        owner_id=model.owner_id,
        parent_id=model.parent_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def folder_to_model(domain: Folder) -> FolderModel:
    return FolderModel(
        id=domain.id,
        owner_id=domain.owner_id,
        parent_id=domain.parent_id,
        name=domain.name,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
