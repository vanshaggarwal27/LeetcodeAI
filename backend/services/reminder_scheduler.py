import os

from apscheduler.schedulers.background import BackgroundScheduler

from alerts.progress_checker import check_unsolved_users

SCHEDULER_INTERVAL_MINUTES = int(os.getenv("REMINDER_SCHEDULER_INTERVAL_MINUTES", "15"))

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        check_unsolved_users,
        "interval",
        minutes=SCHEDULER_INTERVAL_MINUTES,
        id="enqueue_due_reminder_checks",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
