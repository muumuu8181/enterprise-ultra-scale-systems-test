from celery import Celery
from src.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.task_routes = {
    "src.worker.test_celery": "main-queue"
}

@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"
