"""Favorite services."""

import logging

from django.db.models import Count, Prefetch, QuerySet

from core.models import Favorite, FavoriteID, User, Wishlist

logger = logging.getLogger(__name__)


class FavoriteService:
    """Favorite service: The Core’s favorite service provides functions for
    handling favorite model entities and favorite-related business logic.
    """

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
        return Favorite.objects.get(id_field=id)

    @staticmethod
    def query_favorites_for_user(*, user: User) -> QuerySet[Favorite]:
        """Returns a lazy collection of favorites whose user is the specified
        user. Prefetches to favorited wish list and annotates the number of
        wishes per list.

        The collection of favorites is ordered by the wish list’s name.

        Arguments:
            user: User of the favorites to query for.

        Returns:
            Lazy collection of favorites.
        """
        return (
            Favorite.objects.prefetch_related(
                Prefetch(
                    Favorite.Fields.WISHLIST,
                    queryset=Wishlist.objects.annotate(
                        wishes_count=Count(Wishlist.Fields.WISHES),
                    ),
                )
            )
            .filter(user=user)
            .order_by("wishlist__name_field")
        )

    @staticmethod
    def query_favorites_for_wishlist(*, wishlist: Wishlist) -> QuerySet[Favorite]:
        """Returns a lazy collection of favorites for the specified wish list.
        Selects related user.

        Arguments:
            wishlist: Wishlist for the favorites to query for.

        Returns:
            Lazy collection of favorites.
        """
        return Favorite.objects.select_related(Favorite.Fields.USER).filter(wishlist=wishlist)

    @staticmethod
    def count_favorites_for_user(*, user: User) -> int:
        """Counts the number of favorites whose user is the specified user.

        Arguments:
            user:  User of the favorites to count.

        Returns:
            Number of favorites found.
        """
        return Favorite.objects.filter(user=user).count()

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
        return Favorite.objects.filter(user=user, wishlist=wishlist).exists()
