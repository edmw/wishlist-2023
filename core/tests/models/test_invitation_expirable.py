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

    def __init__(self, created_at: datetime.datetime | None):
        self.created_at = created_at


@freeze_time(TZ_NOW)
def test_expired(settings: Any) -> None:
    settings.EXPIRES_TIMEOUT = 60
    invitation = InvitationMock(
        created_at=timezone.now() - datetime.timedelta(seconds=60),
    )
    assert invitation.expired is True


@freeze_time(TZ_NOW)
def test_not_expired_recently_created(settings: Any) -> None:
    settings.EXPIRES_TIMEOUT = 60
    invitation = InvitationMock(
        created_at=timezone.now() - datetime.timedelta(seconds=30),
    )
    assert invitation.expired is False


@freeze_time(TZ_NOW)
def test_not_expired_without_creation_time() -> None:
    """An instance that has not been persisted yet cannot be expired."""
    invitation = InvitationMock(created_at=None)
    assert invitation.expired is False


@freeze_time(TZ_NOW)
def test_expired_missing_setting() -> None:
    invitation = InvitationMock(
        created_at=timezone.now() - datetime.timedelta(seconds=60),
    )
    with pytest.raises(AttributeError):
        assert invitation.expired is True


def test_expires_after_seconds(settings: Any) -> None:
    settings.EXPIRES_TIMEOUT = 60
    assert InvitationMock.expires_after_seconds() == 60
