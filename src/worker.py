from celery import Celery
import os

celery = Celery(
    "worker",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

celery.conf.task_routes = {
    "src.api.v1.wind.*": {"queue": "wind_tasks"},
}

celery.autodiscover_tasks(['src.api.v1.wind'])
