import asyncio
import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import motor.motor_asyncio
import pytz
import requests

from alerts.elevenlabs_service import generate_message
from alerts.twilio_service import send_whatsapp_message

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client.leetcodeai

TARGET_REMINDER_HOUR = int(os.getenv("REMINDER_TARGET_HOUR", "23"))
DEFAULT_TIMEZONE = "Asia/Kolkata"
MAX_DUE_USERS_PER_TICK = int(os.getenv("REMINDER_SCHEDULER_BATCH_SIZE", "1000"))


def safe_zoneinfo(timezone_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def local_reminder_date(user: dict, now_utc: datetime | None = None) -> str:
    now_utc = now_utc or datetime.now(timezone.utc)
    user_zone = safe_zoneinfo(user.get("timezone"))
    return now_utc.astimezone(user_zone).date().isoformat()


def due_timezones(
    now_utc: datetime | None = None,
    target_hour: int = TARGET_REMINDER_HOUR,
) -> list[str]:
    now_utc = now_utc or datetime.now(timezone.utc)
    due: list[str] = []

    for timezone_name in pytz.all_timezones:
        local_now = now_utc.astimezone(safe_zoneinfo(timezone_name))
        if local_now.hour == target_hour:
            due.append(timezone_name)

    return due


async def _load_user(user_id: str) -> dict | None:
    preference = await db.preferences.find_one({"user_id": user_id}, {"_id": 0})
    user = await db.users.find_one({"id": user_id}, {"_id": 0})

    if not preference and not user:
        return None

    return {
        **(user or {}),
        **(preference or {}),
        "id": user_id,
        "user_id": user_id,
    }


async def _has_published_today(user: dict, now_utc: datetime) -> bool:
    user_zone = safe_zoneinfo(user.get("timezone"))
    local_today = now_utc.astimezone(user_zone).date()
    start_utc = datetime.combine(local_today, time.min, user_zone).astimezone(
        timezone.utc
    )
    end_utc = datetime.combine(local_today, time.max, user_zone).astimezone(
        timezone.utc
    )

    query = {
        "date": {
            "$gte": start_utc.isoformat(),
            "$lte": end_utc.isoformat(),
        }
    }
    author = user.get("leetcode_username") or user.get("name") or user.get("email")
    if author:
        query["author"] = author

    return await db.problem_info.count_documents(query) > 0


async def _has_leetcode_submission_today(user: dict, now_utc: datetime) -> bool:
    lc_username = user.get("leetcode_username")
    if not lc_username:
        return False

    user_zone = safe_zoneinfo(user.get("timezone"))
    local_today = now_utc.astimezone(user_zone).date()
    midnight_utc = datetime.combine(local_today, time.min, user_zone).astimezone(
        timezone.utc
    )
    midnight_timestamp = int(midnight_utc.timestamp())

    def check_leetcode() -> dict:
        query = """
        query($username: String!, $limit: Int!) {
          recentAcSubmissionList(username: $username, limit: $limit) {
            timestamp
          }
        }
        """
        response = requests.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": lc_username, "limit": 10}},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    data = await asyncio.to_thread(check_leetcode)
    submissions = data.get("data", {}).get("recentAcSubmissionList", [])
    return any(int(sub["timestamp"]) >= midnight_timestamp for sub in submissions)


async def _send_alert(user: dict) -> None:
    phone = user.get("whatsapp_number")
    if not phone:
        return

    name = user.get("name") or user.get("email") or "User"
    message = generate_message(name)

    await asyncio.to_thread(send_whatsapp_message, phone, message)

    try:
        from alerts.elevenlabs_service import generate_audio
        from alerts.twilio_service import make_call

        try:
            audio_file = await asyncio.to_thread(generate_audio, message)
            backend_url = os.getenv(
                "BACKEND_URL", "https://leetcodeai-backend.onrender.com"
            )
            audio_url = f"{backend_url.rstrip('/')}/{audio_file}"
            await asyncio.to_thread(make_call, phone, audio_url=audio_url)
        except Exception:
            await asyncio.to_thread(make_call, phone, text_to_say=message)
    except Exception as exc:
        print(f"Failed to place reminder call for {phone}: {exc}")


async def check_user_progress_and_alert(
    user_id: str,
    now_utc: datetime | None = None,
) -> dict:
    now_utc = now_utc or datetime.now(timezone.utc)
    user = await _load_user(user_id)

    if not user:
        return {"status": "skipped", "reason": "user_not_found", "user_id": user_id}
    if not user.get("is_opted_in", True):
        return {"status": "skipped", "reason": "not_opted_in", "user_id": user_id}

    reminder_date = local_reminder_date(user, now_utc)
    alert_key = f"{user_id}:{reminder_date}"

    if await db.reminder_alerts.find_one({"key": alert_key}, {"_id": 0}):
        return {"status": "skipped", "reason": "already_alerted", "user_id": user_id}

    has_solved = await _has_published_today(user, now_utc)
    if not has_solved:
        try:
            has_solved = await _has_leetcode_submission_today(user, now_utc)
        except Exception as exc:
            print(f"Failed to check LeetCode for {user_id}: {exc}")

    if has_solved:
        return {"status": "ok", "reason": "completed", "user_id": user_id}

    await _send_alert(user)
    await db.reminder_alerts.update_one(
        {"key": alert_key},
        {
            "$set": {
                "key": alert_key,
                "user_id": user_id,
                "reminder_date": reminder_date,
                "sent_at": now_utc.isoformat(),
            }
        },
        upsert=True,
    )
    return {"status": "alerted", "user_id": user_id}


async def find_due_reminder_users(
    now_utc: datetime | None = None,
    limit: int = MAX_DUE_USERS_PER_TICK,
) -> list[dict]:
    zones = due_timezones(now_utc)
    if not zones:
        return []

    cursor = db.preferences.find(
        {
            "is_opted_in": True,
            "timezone": {"$in": zones},
            "user_id": {"$exists": True},
        },
        {"_id": 0},
    )
    return await cursor.to_list(length=limit)


async def enqueue_due_reminders(now_utc: datetime | None = None) -> dict:
    now_utc = now_utc or datetime.now(timezone.utc)
    due_users = await find_due_reminder_users(now_utc)

    queued = 0
    skipped = 0

    from tasks.reminder_tasks import check_user_progress_and_alert_task

    for user in due_users:
        user_id = user.get("user_id")
        if not user_id:
            skipped += 1
            continue

        queue_key = f"{user_id}:{local_reminder_date(user, now_utc)}"
        if await db.reminder_jobs.find_one({"key": queue_key}, {"_id": 0}):
            skipped += 1
            continue
        # Check if there is a blog post created today
        # Date is stored as ISO format string, we can do a regex or range query
        # Since it's stored as '2026-05-23T...', we can do a prefix match
        today_str = today.isoformat()

        solved_today_count = await db.problem_info.count_documents({
            "date": {"$regex": f"^{today_str}"}
        })

        has_solved = solved_today_count > 0

        # Also check Leetcode submissions
        lc_username = user.get("leetcode_username", "vanshaggarwal27")
        if not has_solved and lc_username:
            try:
                import requests
                # import asyncio
                # import datetime
                import asyncio
                import datetime

                import requests

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

                # Check if any submission has a timestamp from today (UTC)
                # midnight_utc = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
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
            # Not solved today, send reminder!
            name = "Vansh" # Fallback or could add name to DB
            message = generate_message(name)

            print("Triggering alert for:", name)
            print(message)
            try:
                send_whatsapp_message(phone, message)
                print(f"WhatsApp message sent successfully to {phone}!")
            except Exception as e:
                print(f"Failed to send WhatsApp message to {phone}:", e)

            try:
                # 1. Try to Generate Audio via ElevenLabs
                from alerts.elevenlabs_service import generate_audio
                from alerts.twilio_service import make_call

                print("Generating audio via ElevenLabs...")
                try:
                    audio_file = generate_audio(message)

                    # 2. Construct public URL to the static file
                    backend_url = os.getenv("BACKEND_URL", "https://leetcodeai-backend.onrender.com")
                    if backend_url.endswith("/"):
                        backend_url = backend_url[:-1]

                    audio_url = f"{backend_url}/{audio_file}"
                    print(f"Audio available at: {audio_url}, making voice call...")

                    call_sid = make_call(phone, audio_url=audio_url)
                    print(f"Call placed successfully with ElevenLabs to {phone}, SID: {call_sid}")
                except Exception as el_err:
                    print("ElevenLabs failed (possibly Free Tier VPN block):", el_err)
                    print("Falling back to standard Twilio Robot Voice...")
                    # Fallback to standard Twilio voice
                    call_sid = make_call(phone, text_to_say=message)
                    print(f"Call placed successfully with Twilio TTS to {phone}, SID: {call_sid}")

            except Exception as e:
                print(f"Failed to generate audio or make call to {phone}:", e)

        else:
            print(f"User {phone} has already solved {solved_today_count} problems today!")

def check_unsolved_users():
    asyncio.run(_check_unsolved_users_async())


    return {"queued": queued, "skipped": skipped, "due_users": len(due_users)}

def check_unsolved_users() -> dict:
    return asyncio.run(enqueue_due_reminders())
