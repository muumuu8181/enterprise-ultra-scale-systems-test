import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("fire_ops", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def dispatch_units(incident_id: int):
    # Logic to dispatch units would go here
    print(f"Dispatching units for incident {incident_id}")
    return {"status": "dispatched", "incident_id": incident_id}
