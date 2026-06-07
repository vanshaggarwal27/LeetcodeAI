from datetime import datetime, timezone

import pytest
import pytest
from datetime import datetime, timezone


@pytest.mark.parametrize(
    "utc_time,expected_timezone",
    [
        (datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc), "Asia/Kolkata"),
        (datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc), "UTC"),
        (datetime(2026, 1, 2, 4, 0, tzinfo=timezone.utc), "America/New_York"),
    ],
)
def test_due_timezones_multiple_regions(utc_time, expected_timezone):
    from alerts.progress_checker import due_timezones

    zones = due_timezones(utc_time)

    assert expected_timezone in zones


def test_due_timezones_includes_local_11pm_zone():
    
    from alerts.progress_checker import due_timezones

    zones = due_timezones(datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc))

    assert "Asia/Kolkata" in zones
def test_due_timezones_includes_utc():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(
        datetime(2026, 1, 1, 23, 0, tzinfo=timezone.utc)
    )

    assert "UTC" in zones


def test_due_timezones_includes_new_york():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(
        datetime(2026, 1, 2, 4, 0, tzinfo=timezone.utc)
    )

    assert "America/New_York" in zones


def test_due_timezones_includes_los_angeles():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(
        datetime(2026, 1, 2, 7, 0, tzinfo=timezone.utc)
    )

    assert "America/Los_Angeles" in zones


def test_due_timezones_year_end_boundary():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(
        datetime(2026, 12, 31, 17, 30, tzinfo=timezone.utc)
    )

    assert "Asia/Kolkata" in zones


@pytest.mark.asyncio
async def test_find_due_reminder_users_filters_by_timezone(app_module):
    from alerts import progress_checker

    app_module.db.preferences.records.extend(
        [
            {
                "user_id": "due-user",
                "is_opted_in": True,
                "timezone": "Asia/Kolkata",
                "whatsapp_number": "+911234567890",
            },
            {
                "user_id": "not-due-user",
                "is_opted_in": True,
                "timezone": "UTC",
                "whatsapp_number": "+10000000000",
            },
        ]
    )
    progress_checker.db = app_module.db

    users = await progress_checker.find_due_reminder_users(
        datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    )

    assert [user["user_id"] for user in users] == ["due-user"]


@pytest.mark.asyncio
async def test_enqueue_due_reminders_dedupes_jobs(app_module, mocker):
    from alerts import progress_checker

    app_module.db.preferences.records.append(
        {
            "user_id": "due-user",
            "is_opted_in": True,
            "timezone": "Asia/Kolkata",
            "whatsapp_number": "+911234567890",
        }
    )
    progress_checker.db = app_module.db

    task = mocker.patch(
        "tasks.reminder_tasks.check_user_progress_and_alert_task.delay",
        autospec=True,
    )

    now = datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    first = await progress_checker.enqueue_due_reminders(now)
    second = await progress_checker.enqueue_due_reminders(now)

    assert first["queued"] == 1
    assert second["queued"] == 0
    task.assert_called_once_with("due-user")
@pytest.mark.asyncio
async def test_find_due_reminder_users_skips_null_timezone(app_module):
    from alerts import progress_checker

    app_module.db.preferences.records.append(
        {
            "user_id": "user1",
            "is_opted_in": True,
            "timezone": None,
            "whatsapp_number": "+911234567890",
        }
    )

    progress_checker.db = app_module.db

    users = await progress_checker.find_due_reminder_users(
        datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    )

    assert users == []

@pytest.mark.asyncio
async def test_find_due_reminder_users_skips_empty_timezone(app_module):
    from alerts import progress_checker

    app_module.db.preferences.records.append(
        {
            "user_id": "user1",
            "is_opted_in": True,
            "timezone": "",
            "whatsapp_number": "+911234567890",
        }
    )

    progress_checker.db = app_module.db

    users = await progress_checker.find_due_reminder_users(
        datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    )

    assert users == []
@pytest.mark.asyncio
async def test_find_due_reminder_users_skips_missing_whatsapp(app_module):
    from alerts import progress_checker

    app_module.db.preferences.records.append(
        {
            "user_id": "user1",
            "is_opted_in": True,
            "timezone": "Asia/Kolkata",
            "whatsapp_number": None,
        }
    )

    progress_checker.db = app_module.db

    users = await progress_checker.find_due_reminder_users(
        datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    )

    assert users == []
@pytest.mark.asyncio
async def test_find_due_reminder_users_skips_invalid_timezone(app_module):
    from alerts import progress_checker

    app_module.db.preferences.records.append(
        {
            "user_id": "user1",
            "is_opted_in": True,
            "timezone": "INVALID_TIMEZONE",
            "whatsapp_number": "+911234567890",
        }
    )

    progress_checker.db = app_module.db

    users = await progress_checker.find_due_reminder_users(
        datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    )

    assert users == []
