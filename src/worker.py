from celery import Celery
import os

# Configure Redis backend
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    "zoo_worker",
    broker=REDIS_URL,
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

@celery_app.task
def process_maintenance_schedule(enclosure_id):
    # Mock task
    return f"Processed maintenance for enclosure {enclosure_id}"
