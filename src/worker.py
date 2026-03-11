from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Initialize Celery app
# The variable name 'app' or 'celery' is expected by the CLI unless specified (e.g. -A src.worker:app)
# But standard is usually 'app'.
app = Celery("sharing_worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# Configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

if __name__ == "__main__":
    app.start()
