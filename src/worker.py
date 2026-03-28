import os
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("worker", broker=broker_url, backend=backend_url)

@app.task
def dummy_task():
    return "Task completed"
