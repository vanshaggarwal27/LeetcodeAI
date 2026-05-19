from apscheduler.schedulers.background import BackgroundScheduler

from alerts.progress_checker import check_unsolved_users

scheduler = BackgroundScheduler()

scheduler.add_job(
    check_unsolved_users,
    "interval",
    minutes=1
)

scheduler.start()
