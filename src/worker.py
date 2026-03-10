import os
from celery import Celery

app = Celery("immigration_worker")

app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

@app.task
def process_visa_application(application_id: int):
    # Dummy task
    return f"Processed application {application_id}"
