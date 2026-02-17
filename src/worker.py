import os
from celery import Celery

celery_app = Celery(
    "worker",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def mock_simulation_task(job_id: int):
    # This would simulate the job
    print(f"Executing job {job_id}")
    return {"status": "completed"}
