from time import timezone

from alerts.progress_checker import check_unsolved_users
from services.reminder_scheduler import BackgroundScheduler, start_scheduler

scheduler = BackgroundScheduler()

# Check daily at 11:00 PM IST
scheduler.add_job(
    check_unsolved_users, "cron", hour=23, minute=0, timezone=timezone("Asia/Kolkata")
)

scheduler.start()
start_scheduler()
