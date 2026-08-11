from __future__ import annotations

import asyncio

from celery import shared_task

from app.application.cleanup_service import CleanupService
from app.application.transfer_codes import TransferCodeGenerator
from app.application.uow import SQLAlchemyUnitOfWork
from app.core.settings import get_settings
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.storage.local import LocalFileStorage


@shared_task(name="app.infrastructure.tasks.cleanup.cleanup_expired_transfers")
def cleanup_expired_transfers() -> int:
    settings = get_settings()
    session_factory = get_session_factory(settings.database_url)
    uow = SQLAlchemyUnitOfWork(session_factory, settings.redis_url)
    file_storage = LocalFileStorage(settings.uploads_dir)
    service = CleanupService(uow=uow, file_storage=file_storage)
    return asyncio.run(service.cleanup_expired_transfers())
