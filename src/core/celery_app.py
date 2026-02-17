from celery import Celery
from celery.schedules import crontab
from src.core.config import settings

celery_app = Celery(
    "banking_core",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    imports=["src.workers.celery_tasks"],
)

# Beat Schedule
celery_app.conf.beat_schedule = {
    "process_batch_transfer_daily": {
        "task": "process_batch_transfer",
        "schedule": crontab(hour=9, minute=0),
    },
    "generate_monthly_statement_monthly": {
        "task": "generate_monthly_statement",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
    },
}
