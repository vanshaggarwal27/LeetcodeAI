import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "leetlog_ai",
    broker=os.getenv("CELERY_BROKER_URL", redis_url),
    backend=os.getenv("CELERY_RESULT_BACKEND", redis_url),
    include=["tasks.reminder_tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_default_queue="reminders",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)
