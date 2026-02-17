from celery import Celery
import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("transplant_worker", broker=broker_url, backend=backend_url)

@app.task
def process_organ_match(organ_id: int):
    # Dummy task implementation
    return f"Processing match for organ {organ_id}"
