import asyncio
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import motor.motor_asyncio
import pytz
import requests

from alerts.elevenlabs_service import generate_message
from alerts.twilio_service import send_whatsapp_message

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
        message = generate_message(name)

        print("Triggering alert for:", name)
        print(message)
        try:
            send_whatsapp_message(phone, message)
            print(f"WhatsApp message sent successfully to {phone}!")
        except Exception as e:
            print(f"Failed to send WhatsApp message to {phone}:", e)

        try:
            from alerts.elevenlabs_service import generate_audio
            from alerts.twilio_service import make_call

            print("Generating audio via ElevenLabs...")
            try:
                audio_file = generate_audio(message)
                backend_url = os.getenv("BACKEND_URL", "https://leetcodeai-backend.onrender.com")
                if backend_url.endswith("/"):
                    backend_url = backend_url[:-1]

                audio_url = f"{backend_url}/{audio_file}"
                print(f"Audio available at: {audio_url}, making voice call...")

                call_sid = make_call(phone, audio_url=audio_url)
                print(f"Call placed successfully with ElevenLabs to {phone}, SID: {call_sid}")
            except Exception as el_err:
                print("ElevenLabs failed:", el_err)
                call_sid = make_call(phone, text_to_say=message)
                print(f"Call placed successfully with Twilio TTS to {phone}, SID: {call_sid}")
        except Exception as e:
            print(f"Failed to generate audio or make call to {phone}:", e)
    else:
        print(f"User {phone} has already solved {solved_today_count} problems today!")


async def _check_unsolved_users_async():
    cursor = db.preferences.find({"is_opted_in": True})
    users = await cursor.to_list(length=100)
    today = datetime.now(timezone.utc).date()
    tasks = [process_single_user(user, today) for user in users]
    await asyncio.gather(*tasks)


def check_unsolved_users():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(_check_unsolved_users_async())
    else:
        asyncio.run(_check_unsolved_users_async())
