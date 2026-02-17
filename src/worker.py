from celery import Celery
from src.core.config import settings

celery = Celery(
    "game_worker",
    broker=settings.celery_broker_url,
    backend=settings.redis_url
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
