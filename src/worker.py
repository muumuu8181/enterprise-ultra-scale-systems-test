from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery("worker", broker=CELERY_BROKER_URL)

@celery_app.task
def dummy_task():
    pass
