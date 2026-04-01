from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task
def dummy_task():
    return "ok"
