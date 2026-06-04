import asyncio

from alerts.progress_checker import check_user_progress_and_alert
from celery_app import celery_app


@celery_app.task(
    name="reminders.check_user_progress_and_alert",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def check_user_progress_and_alert_task(user_id: str) -> dict:
    return asyncio.run(check_user_progress_and_alert(user_id))
