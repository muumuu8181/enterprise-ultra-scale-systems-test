import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery("scf_platform", broker=broker_url, backend=result_backend)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@app.task(name="process_invoice")
def process_invoice(invoice_id):
    return f"Processed invoice {invoice_id}"
