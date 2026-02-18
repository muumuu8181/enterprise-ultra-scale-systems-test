from celery import Celery
from src.core.config import settings

# This 'app' instance is what 'celery -A src.worker' looks for.
app = Celery("food_delivery_worker", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

# Optional: Autodiscover tasks if we had any tasks modules
# app.autodiscover_tasks(['src.services'])
