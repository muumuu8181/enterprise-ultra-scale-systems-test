from celery import Celery
import os

celery_app = Celery("content_moderation", broker=os.environ.get("CELERY_BROKER_URL"))
celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
