from django.db import models

from ._uuid import UUIDFieldMixin


class WishlistIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a wishlist’s identifier."""

    description = "Unique ID of a Wishlist"
