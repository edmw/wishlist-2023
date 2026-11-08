"""Mixin for invitations that want to provide a fixed expiration duration."""

import datetime
from typing import Protocol

from django.conf import settings as django_settings
from django.utils import timezone


class HasSentAt(Protocol):
    sent_at: datetime.datetime | None


class ExpiresAfterFixedTimeProtocol(HasSentAt, Protocol):
    @property
    # The member mirrors the class attribute name of the concrete models.
    def EXPIRES_AFTER_SETTINGS_KEY(self) -> str: ...  # noqa: N802


class ExpiresAfterFixedTime:
    """Mixin for invitations that want to provide a fixed expiration duration.

    The invitation type needs to provide a key with which the expiry duration
    in seconds can be taken from the settings of the project, and a `sent_at`
    attribute holding the time at which it was sent (or `None` if not yet).
    """

    EXPIRES_AFTER_SETTINGS_KEY = "EXPIRES_AFTER"
    sent_at: datetime.datetime | None  # Provided by the concrete model.

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

    @classmethod
    def expires_after_seconds(cls) -> int:
        """Returns the configured expiration duration in seconds.

        The duration is read from the settings key referenced by this
        invitation type, so that the value always matches the actual
        expiration rule.

        Returns:
            Expiration duration in seconds.
        """
        return getattr(django_settings, cls.EXPIRES_AFTER_SETTINGS_KEY)
