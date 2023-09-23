"""Mixin for invitations that want to provide a fixed expiration duration."""

import datetime
from typing import Protocol

from django.conf import settings as django_settings
from django.utils import timezone


class HasSentAt(Protocol):
    sent_at: datetime.datetime


class ExpiresAfterFixedTimeProtocol(HasSentAt, Protocol):
    EXPIRES_AFTER_SETTINGS_KEY: str


class ExpiresAfterFixedTime:
    """Mixin for invitations that want to provide a fixed expiration duration.

    The invitation type needs to provide a key with which the expiry duration
    in seconds can be taken from the settings of the project.
    """

    EXPIRES_AFTER_SETTINGS_KEY = "EXPIRES_AFTER"

    @property
    def expired(self: ExpiresAfterFixedTimeProtocol) -> bool:
        if self.sent_at:
            expires_after = getattr(django_settings, self.EXPIRES_AFTER_SETTINGS_KEY)

            delta = timezone.now() - self.sent_at
            # Is expired if the invitation was sent more than configured number
            # of seconds ago.
            return delta.total_seconds() >= expires_after

        # Is not expired if the invitation has not yet been sent.
        return False
