import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import motor.motor_asyncio
import pytz
import requests

from alerts.elevenlabs_service import generate_message

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client.leetcodeai

# --- ORIGINAL UNTOUCHED FUNCTIONS REQUIRING IMPORT BY PYTEST ---

def due_timezones(current_time: datetime = None) -> list[str]:
    """Find target timezones where the local time matches the alert schedule window."""
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    target_hour = 23  # 11 PM target
    target_minute = 0

    matched = []
    for tz_name in pytz.all_timezones:
        try:
            localized = current_time.astimezone(ZoneInfo(tz_name))
            if localized.hour == target_hour and localized.minute == target_minute:
                matched.append(tz_name)
        except (ZoneInfoNotFoundError, Exception):
            continue
    return matched


async def find_due_reminder_users(target_hour: int = 23) -> list:
    """Fetch all opted-in users matching the specific localized target schedule."""
    now_utc = datetime.now(timezone.utc)
    valid_timezones = due_timezones(now_utc)

    cursor = db.preferences.find({
        "is_opted_in": True,
        "timezone": {"$in": valid_timezones}
    })
    return await cursor.to_list(length=1000)


async def check_user_progress_and_alert(user, today):
    """Legacy individual task wrapper mapping to the parallel worker logic."""
    await process_single_user(user, today)


# --- YOUR PARALLELIZED IMPLEMENTATION CONTEXT ---

async def process_single_user(user, today):
    """Worker function to process progress checking and alerts for a single user."""
    phone = user.get("whatsapp_number")
    if not phone:
        return

    today_str = today.isoformat()
    solved_today_count = await db.problem_info.count_documents({
        "date": {"$regex": f"^{today_str}"}
    })
    has_solved = solved_today_count > 0

    lc_username = user.get("leetcode_username", "vanshaggarwal27")
    if not has_solved and lc_username:
        try:
            def check_lc():
                query = """
                query($username: String!, $limit: Int!) {
                  recentAcSubmissionList(username: $username, limit: $limit) {
                    timestamp
                  }
                }
                """
                return requests.post("https://leetcode.com/graphql", json={
                    "query": query,
                    "variables": {"username": lc_username, "limit": 10}
                }, timeout=10).json()

            data = await asyncio.to_thread(check_lc)
            submissions = data.get("data", {}).get("recentAcSubmissionList", [])

            midnight_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            midnight_timestamp = int(midnight_utc.timestamp())

            for sub in submissions:
                if int(sub["timestamp"]) >= midnight_timestamp:
                    has_solved = True
                    print(f"Found recent Leetcode submission today for {lc_username}!")
                    break
        except Exception as e:
            print(f"Failed to check Leetcode for {lc_username}:", e)

    if not has_solved:
        name = user.get("name", "User")
        generate_message(name)


