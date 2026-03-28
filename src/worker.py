import os
from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)

@celery.task
def process_checkin(passenger_id):
    # Mock task
    print(f"Processing checkin for passenger {passenger_id}")
    return True
