from celery import Celery
import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("mlops_worker", broker=broker_url, backend=backend_url)

@celery_app.task
def train_model(model_id):
    return f"Model {model_id} training started"
