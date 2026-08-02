"""Model class representing a favorite wish lists."""

import logging

from django.conf import settings as django_settings
from django.db import models
from django.urls import reverse

from core import constants
from core.models import fields, types
from core.models._base import IDMixin
from core.models.wishlist import Wishlist

logger = logging.getLogger(__name__)


class Favorite(IDMixin[types.FavoriteID], models.Model):
    """Model used to represent a favorite persisted in database."""

    MAXIMUM_NUMBER_OF_FAVORITES_PER_USER = 100

    id_type = types.FavoriteID
    id_field = fields.FavoriteIDField()

    # Relations

    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="favorites"
    )
    user_id: types.UserID

    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="favorites")
    wishlist_id: types.WishlistID

    notify_on_item_create = models.BooleanField(default=False)

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta data for the Favorite model."""

        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "wishlist",
                ],
                name="unique_favorite",
            )
        ]

    class Fields:
        """Field names for the Favorite model."""

        ID = "id_field"
        USER = "user"
        WISHLIST = "wishlist"
        NOTIFY_ON_ITEM_CREATE = "notify_on_item_create"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this favorite.

        Returns:
            Representation text.
        """
        return f"{self.user_id} -> {self.wishlist_id}"

    def __repr__(self) -> str:
        """Returns a string reputation of this favorite.

        Returns:
            Reputation text.
        """
        return (
            f"<{self.__class__.__name__}[{str(self.id)}]: user={self.user_id}; wishlist={self.wishlist_id}>"
        )

    # Custom properties

    def get_absolute_delete_url(self) -> str:
        """Returns the URL for the page to delete this favorite.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_FAVORITE_DELETE,
            kwargs={
                constants.USER_ID_KEY: self.user_id,
                constants.FAVORITE_ID_KEY: self.pk,
            },
        )

    def get_absolute_update_url(self) -> str:
        """Returns the URL for the page to update this favorite.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_FAVORITE_UPDATE,
            kwargs={
                constants.USER_ID_KEY: self.user_id,
                constants.FAVORITE_ID_KEY: self.pk,
            },
        )
