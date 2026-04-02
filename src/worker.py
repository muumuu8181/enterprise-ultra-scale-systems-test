from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)

@celery.task
def process_transaction(tx_id: int):
    # Mock task
    print(f"Processing transaction {tx_id}")
    return True
