from datetime import date, timedelta

from app.config.constants import ADVANCE_DAYS_WINDOWS


def test_advance_windows_are_exactly_five_fixed_values():
    assert ADVANCE_DAYS_WINDOWS == (1, 7, 15, 30, 45)


def test_advance_window_dates_computed_correctly():
    today = date(2026, 9, 15)
    expected = {
        1: date(2026, 9, 16),
        7: date(2026, 9, 22),
        15: date(2026, 9, 30),
        30: date(2026, 10, 15),
        45: date(2026, 10, 30),
    }
    for window in ADVANCE_DAYS_WINDOWS:
        assert today + timedelta(days=window) == expected[window]


def test_scheduler_task_registered_in_celery_app():
    from app.celery_app import celery_app
    import app.scheduler.jobs  # noqa: F401  ensures task is registered via include

    assert "schedule_daily_scrapes" in celery_app.tasks


def test_scraping_task_registered_in_celery_app():
    from app.celery_app import celery_app
    import app.tasks.scraping_tasks  # noqa: F401

    assert "scrape_google_flights" in celery_app.tasks


def test_index_task_registered_in_celery_app():
    from app.celery_app import celery_app
    import app.tasks.index_tasks  # noqa: F401

    assert "calculate_index_windows" in celery_app.tasks
