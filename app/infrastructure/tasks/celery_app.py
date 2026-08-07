from __future__ import annotations

import os

from celery import Celery
from celery.schedules import schedule

from app.core.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "cargo",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.infrastructure.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-transfers": {
            "task": "app.infrastructure.tasks.cleanup.cleanup_expired_transfers",
            "schedule": schedule(run_every=settings.cleanup_interval_seconds),
        }
    },
)
