from django.db import models

from ._uuid import UUIDFieldMixin


class UserIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a user’s identifier."""

    description = "Unique ID of a user"
