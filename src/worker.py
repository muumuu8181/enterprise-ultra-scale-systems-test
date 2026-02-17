from celery import Celery
from src.config import settings

celery = Celery(
    "agri_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery.task
def mock_task(x, y):
    return x + y
