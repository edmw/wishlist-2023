"""Wishlist services."""

import logging

from django.db.models import Count, QuerySet

from core.models import User, Wishlist, WishlistID

logger = logging.getLogger(__name__)


class WishlistService:
    """Wishlist service: The Core’s wishlist service provides functions for
    handling wishlist model entities and wishlist-related business logic.
    """

    @staticmethod
    def query_wishlists_for_user(
        *, user: User, exclude: list[Wishlist] | None = None
    ) -> QuerySet[Wishlist]:
        """Returns a lazy collection of wish lists whose owner is the specified
        user. Annotates the number of wishes per list.

        The collection of wish lists is ordered by the wish list’s names.

        Arguments:
            user: Owner of the lists to query for.
            exclude: List of wish lists to exclude from the result.

        Returns:
            Lazy collection of wish lists.
        """
        queryset = (
            Wishlist.objects.annotate(wishes_count=Count(Wishlist.Fields.WISHES))
            .filter(owner=user)
            .order_by(Wishlist.Fields.NAME)
        )
        if exclude:
            queryset = queryset.exclude(pk__in=[list.pk for list in exclude])
        return queryset

    @staticmethod
    def count_wishlists_for_user(*, user: User) -> int:
        """Counts the number of wish lists whose owner is the specified user.

        Arguments:
            user:  Owner of the lists to count.

        Returns:
            Number of wish lists found.
        """
        return Wishlist.objects.filter(owner=user).count()

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
        return Wishlist.objects.annotate(wishes_count=Count(Wishlist.Fields.WISHES)).get(id_field=id)
