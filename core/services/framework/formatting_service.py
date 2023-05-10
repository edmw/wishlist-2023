import logging
from datetime import datetime

import humanize
from django.conf import settings as django_settings
from django.utils import timezone
from django.utils.translation import gettext as _

from core.constants import (
    ONE_DAY_IN_SECONDS,
    ONE_HOUR_IN_SECONDS,
    ONE_MINUTE_IN_SECONDS,
    TWO_HOURS_IN_SECONDS,
    TWO_MINUTES_IN_SECONDS,
)

logger = logging.getLogger(__name__)


def _was_just_now(timedelta_seconds: float) -> bool:
    return timedelta_seconds <= 1


def _was_one_minute_ago(timedelta_seconds: float) -> bool:
    return timedelta_seconds >= ONE_MINUTE_IN_SECONDS and timedelta_seconds < TWO_MINUTES_IN_SECONDS


def _was_one_hour_ago(timedelta_seconds: float) -> bool:
    return timedelta_seconds >= ONE_HOUR_IN_SECONDS and timedelta_seconds < TWO_HOURS_IN_SECONDS


def _was_less_than_one_day_ago(timedelta_seconds: float) -> bool:
    return timedelta_seconds < ONE_DAY_IN_SECONDS


class FormattingService:
    @staticmethod
    def format_datetime(*, value: datetime, language_code: str) -> str:
        if format_string := django_settings.FORMAT_DATETIME.get(language_code):
            return value.strftime(format_string)
        else:
            return str(value)

    @staticmethod
    def natural_datetime(*, value: datetime, language_code: str) -> str:
        datetime_local = timezone.localtime(value)
        datetime_delta = timezone.localtime(timezone.now()) - datetime_local
        datetime_delta_seconds = datetime_delta.total_seconds()

        if _was_just_now(datetime_delta_seconds):
            return _("just now")
        elif _was_one_minute_ago(datetime_delta_seconds):
            return _("one minute ago")
        elif _was_one_hour_ago(datetime_delta_seconds):
            return _("one hour ago")
        elif _was_less_than_one_day_ago(datetime_delta_seconds):
            natural_delta = humanize.naturaldelta(datetime_delta)
            return _("{} ago").format(natural_delta)  # noqa:P103
        else:
            return FormattingService.format_datetime(value=value, language_code=language_code)
