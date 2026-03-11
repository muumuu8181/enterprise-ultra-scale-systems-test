from celery import Celery

app = Celery("contracts", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
