from django.db import models

from ._uuid import UUIDFieldMixin


class WishIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a wish’s identifier."""

    description = "Unique ID of a Wish"
