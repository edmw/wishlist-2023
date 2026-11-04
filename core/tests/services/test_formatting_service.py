from datetime import UTC, datetime, timedelta

from freezegun import freeze_time

from core.services import FormattingService


class TestFormatDatetime:
    def test_formats_with_configured_format(self) -> None:
        value = datetime(2025, 12, 30, 12, 0, tzinfo=UTC)
        assert (
            FormattingService.format_datetime(value=value, language_code="en") == "12/30/2025 at 12:00 PM"
        )
        assert (
            FormattingService.format_datetime(value=value, language_code="de") == "30.12.2025 um 12:00 Uhr"
        )

    def test_falls_back_to_str_for_unknown_language(self) -> None:
        value = datetime(2025, 12, 30, 12, 0, tzinfo=UTC)
        assert FormattingService.format_datetime(value=value, language_code="fr") == str(value)


class TestNaturalDatetime:
    @freeze_time("2026-01-01 12:00:00")
    def test_just_now(self) -> None:
        value = datetime.now(UTC)
        assert FormattingService.natural_datetime(value=value, language_code="en") == "just now"

    @freeze_time("2026-01-01 12:00:00")
    def test_one_minute_ago(self) -> None:
        value = datetime.now(UTC) - timedelta(seconds=90)
        assert FormattingService.natural_datetime(value=value, language_code="en") == "one minute ago"

    @freeze_time("2026-01-01 12:00:00")
    def test_one_hour_ago(self) -> None:
        value = datetime.now(UTC) - timedelta(hours=1, minutes=30)
        assert FormattingService.natural_datetime(value=value, language_code="en") == "one hour ago"

    @freeze_time("2026-01-01 12:00:00")
    def test_less_than_one_day_ago(self) -> None:
        value = datetime.now(UTC) - timedelta(hours=5)
        assert FormattingService.natural_datetime(value=value, language_code="en") == "5 hours ago"

    @freeze_time("2026-01-01 12:00:00")
    def test_one_day_or_more_ago_falls_back_to_format(self) -> None:
        value = datetime.now(UTC) - timedelta(days=2)
        assert (
            FormattingService.natural_datetime(value=value, language_code="en") == "12/30/2025 at 12:00 PM"
        )
