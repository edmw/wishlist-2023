"""Wishlist services."""

import logging

from core.models import User, Wishlist, WishlistID, WishlistLens

logger = logging.getLogger(__name__)


class WishlistService:
    """Wishlist service: The Core’s wishlist service provides functions for
    handling wishlist model entities and wishlist-related business logic.
    """

    @staticmethod
    def count_wishlists_for_user(*, user: User) -> int:
        """Counts the number of wish lists whose owner is the specified user.

        Arguments:
            user:  Owner of the lists to count.

        Returns:
            Number of wish lists found.
        """
        return WishlistLens.view().by_owner(user=user).queryset.count()

    @staticmethod
    def get_wishlist(id: WishlistID) -> Wishlist:
        """Gets the wish list with the matching id. Raises an
        `Wishlist.DoesNotExist` exception if a wish list with the specified ID
        does not exist. Annotates the number of wishes.

        Arguments:
            id: The wish list’s identifier to look up.

        Returns:
            A wish list entity.

        Raises:
            Wishlist.DoesNotExist
        """
        return WishlistLens.view().counting_wishes().queryset.get(id_field=id)
