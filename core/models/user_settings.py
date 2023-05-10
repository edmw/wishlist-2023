"""Model class representing user settings."""
from __future__ import annotations

import logging

from django.conf import settings as django_settings
from django.db import models
from django.urls import reverse

from core import constants

from ._base import IDMixin
from .fields import (
    EmailEnabledField,
    PushoverEnabledField,
    PushoverKeyField,
    UserSettingsIDField,
)
from .types import PushoverKey, UserID, UserSettingsID

logger = logging.getLogger(__name__)


class UserSettings(IDMixin[UserSettingsID], models.Model):
    """Model used to represent a user’s settings persisted in database."""

    id_type = UserSettingsID
    id_field = UserSettingsIDField()

    user = models.OneToOneField(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings"
    )
    user_id: UserID

    email_enabled_field = EmailEnabledField()

    pushover_enabled_field = PushoverEnabledField()

    pushover_key_field = PushoverKeyField()

    class Meta:
        """Meta data for the UserSettings model."""

        verbose_name = "User settings"
        verbose_name_plural = "User settings"

    class Fields:
        """Field names for the UserSettings model."""

        ID = "id_field"
        USER = "user"
        EMAIL_ENABLED = "email_enabled_field"
        PUSHOVER_ENABLED = "pushover_enabled_field"
        PUSHOVER_KEY = "pushover_key_field"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this user settings.

        Returns:
            Representation text.
        """
        return f"{self.user_id}"

    def get_absolute_url(self) -> str:
        """Returns the URL for the page to view this settings.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_USER_PROFILE,
            kwargs={constants.USER_ID_KEY: self.user_id},
        )

    # Properties

    @property
    def email_enabled(self) -> bool:
        """The flag for this user’s email notifications.

        Returns:
           True, if email notifications are enabled, false otherwise.
        """
        return bool(self.email_enabled_field)

    @email_enabled.setter
    def email_enabled(self, enabled: bool) -> None:
        """The setter for the flag of this user’s email notifications.

        Arguments:
            enabled: Enable or disable email notifications.
        """
        self.email_enabled_field = enabled

    @property
    def pushover_enabled(self) -> bool:
        """The flag for this user’s pushover notifications.

        Returns:
            True, if pushover notifications are enabled, false otherwise.
        """
        return bool(self.pushover_enabled_field)

    @pushover_enabled.setter
    def pushover_enabled(self, enabled: bool) -> None:
        """The setter for the flag of this user’s pushover notifications.

        Arguments:
            enabled: Enable or disable pushover notifications.
        """
        self.pushover_enabled_field = enabled

    @property
    def pushover_key(self) -> PushoverKey:
        """The key to access Pushover. This computed property returns the
        correctly typed value instead of an indeterminate string.

        Returns:
            The pushover key.
        """
        return PushoverKey(self.pushover_key_field)

    @pushover_key.setter
    def pushover_key(self, pushover_key: PushoverKey) -> None:
        """The setter for the key to access Pushover. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            pushover_key: The pushover key.
        """
        self.pushover_key = pushover_key

    # Custom properties

    @property
    def notifications_enabled(self) -> bool:
        """The flag for this user’s notifications.

        Returns:
            True, if this user has any notifications enabled, fals otherwise.
        """
        return self.email_enabled or self.pushover_enabled
