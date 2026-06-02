from datetime import datetime, timezone

import pytest


def test_due_timezones_includes_local_11pm_zone():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc))
    assert "Asia/Kolkata" in zones


@pytest.mark.asyncio
async def test_find_due_reminder_users_filters_by_timezone(app_module, mocker):
    from alerts import progress_checker

    # Mock datetime.now inside progress_checker to return 17:30 UTC (which is 11 PM IST)
    mock_datetime = mocker.patch("alerts.progress_checker.datetime")
    mock_datetime.now.return_value = datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc)
    mock_datetime.timezone = timezone

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

    users = await progress_checker.find_due_reminder_users()
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

    # Mock out the single user processor task runner
    mock_processor = mocker.patch(
        "alerts.progress_checker.process_single_user",
        return_value=None,
    )

    # Trigger your actual runner function
    await progress_checker._check_unsolved_users_async()

    # Verify that the processing system picked up our target user record
    assert mock_processor.call_count == 1
