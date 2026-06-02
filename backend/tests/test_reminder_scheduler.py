from datetime import datetime, timezone


def test_due_timezones_includes_local_11pm_zone():
    from alerts.progress_checker import due_timezones

    zones = due_timezones(datetime(2026, 1, 1, 17, 30, tzinfo=timezone.utc))

    assert "Asia/Kolkata" in zones


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
