from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("talent_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@app.task
def process_data():
    return "Processed"
