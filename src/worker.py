from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# The name used in docker-compose command `celery -A src.worker ...` implies this module is the entry point.
# Celery will look for an app instance here.
celery = Celery("census_worker", broker=redis_url, backend=redis_url)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery.task
def process_census_data(round_id: int):
    """
    Example task to process census data.
    """
    print(f"Processing census round {round_id}")
    return {"status": "processed", "round_id": round_id}
