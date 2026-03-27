from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery("clinical_trials", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@app.task(name="process_event")
def process_event(event_data):
    # Dummy processing logic
    print(f"Processing event: {event_data}")
    return "processed"
