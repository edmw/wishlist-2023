from django.db import models

from ._uuid import UUIDFieldMixin


class UserSettingsIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a user’s settings’ identifier."""

    description = "Unique ID of a user’s settings"
