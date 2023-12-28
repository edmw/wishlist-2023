import datetime
import zoneinfo
from typing import Any

import pytest
from django.conf import settings as django_settings
from django.utils import timezone
from freezegun import freeze_time

from core.models.invitation_expirable import ExpiresAfterFixedTime

TZ = zoneinfo.ZoneInfo(django_settings.TIME_ZONE)
TZ_NOW = datetime.datetime.now(TZ)


class InvitationMock(ExpiresAfterFixedTime):
    EXPIRES_AFTER_SETTINGS_KEY = "EXPIRES_TIMEOUT"

    expired: bool

    def __init__(self, sent_at: datetime.datetime | None):
        self.sent_at = sent_at


@freeze_time(TZ_NOW)
def test_expired(settings: Any) -> None:
    settings.EXPIRES_TIMEOUT = 60
    invitation = InvitationMock(
        sent_at=timezone.now() - datetime.timedelta(seconds=60),
    )
    assert invitation.expired is True


@freeze_time(TZ_NOW)
def test_expired_not_sent() -> None:
    invitation = InvitationMock(sent_at=None)
    assert invitation.expired is False


@freeze_time(TZ_NOW)
def test_expired_missing_setting() -> None:
    invitation = InvitationMock(
        sent_at=timezone.now() - datetime.timedelta(seconds=60),
    )
    with pytest.raises(AttributeError):
        assert invitation.expired is True
