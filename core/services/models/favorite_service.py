"""Favorite services."""

import logging

from core.models import Favorite, FavoriteID, FavoriteLens, User, Wishlist

logger = logging.getLogger(__name__)


class FavoriteService:
    """Favorite service: The Core’s favorite service provides functions for
    handling favorite model entities and favorite-related business logic.
    """

    @staticmethod
    def count_favorites_for_user(*, user: User) -> int:
        """Counts the number of favorites whose user is the specified user.

        Arguments:
            user: User of the favorites to count.

        Returns:
            Number of favorites found.
        """
        return FavoriteLens.view().by_user(user=user).count()

    @staticmethod
    def get_favorite(id: FavoriteID) -> Favorite:
        """Gets the favorite with the matching id. Raises an
        `Favorite.DoesNotExist` exception if a favorite with the specified ID
        does not exist.

        Arguments:
            id: The favorite’s identifier to look up.

        Returns:
            A favorite entity.

        Raises:
            Favorite.DoesNotExist
        """
        return FavoriteLens.view().by_id(id=id).one()

    @staticmethod
    def is_favorite(*, user: User, wishlist: Wishlist) -> bool:
        """Checks, if the given wishlist is a favorite wish list of the
        specified user.

        Arguments:
            user: User to check the favorite for.
            wishlist: Wishlist which may be a favorite.

        Returns:
            True, if the specified wish list is a favorite, otherwise False.
        """
        return FavoriteLens.view().by_user(user=user).by_wishlist(wishlist=wishlist).exists()
