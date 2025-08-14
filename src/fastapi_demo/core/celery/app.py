from celery import Celery

from fastapi_demo.core.celery.config import make_config
from fastapi_demo.core.config import settings

celery_app = Celery(
    settings.CELERY_APP_NAME,
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_REDIS_URI),
)

celery_app.conf.update(make_config())
celery_app.autodiscover_tasks(packages=["fastapi_demo.core.celery.tasks"], related_name=None)
