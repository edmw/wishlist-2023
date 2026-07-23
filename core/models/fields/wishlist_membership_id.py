from django.db import models

from ._uuid import UUIDFieldMixin


class WishlistMembershipIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a wishlist membership’s identifier."""

    description = "Unique ID of a WishlistMembership"
