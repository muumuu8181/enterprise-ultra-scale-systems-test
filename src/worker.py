from celery import Celery
import os

celery_app = Celery("worker", broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))
celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

if __name__ == '__main__':
    celery_app.start()
