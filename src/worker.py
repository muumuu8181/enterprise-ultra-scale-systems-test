from celery import Celery
import os

# Use Redis as the broker and backend
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery("finance_worker", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Example task to make sure worker starts
@celery_app.task(name="test_task")
def test_task(x, y):
    return x + y
