from django.db import models

from ._uuid import UUIDFieldMixin


class FavoriteIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a favorite’s identifier."""

    description = "Unique ID of a favorite"
