from apscheduler.schedulers.background import BackgroundScheduler

from utils.progress_checker import has_completed_daily_problem

scheduler = BackgroundScheduler()

def check_daily_progress():
    user_id = "demo-user"

    completed = has_completed_daily_problem(user_id)

    if not completed:
        print("User missed daily problem. Trigger reminder call.")

scheduler.add_job(check_daily_progress, "interval", minutes=60)

def start_scheduler():
    scheduler.start()
