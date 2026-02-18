import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "ai_ml_platform",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=os.getenv("CELERY_ALWAYS_EAGER", "False").lower() == "true",
)

if __name__ == "__main__":
    celery_app.start()
