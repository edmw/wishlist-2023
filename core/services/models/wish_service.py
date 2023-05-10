"""Wish services."""

import logging

from django.db.models import QuerySet
from django.utils import timezone

from core.models import Wish, WishID, Wishlist
from core.models.types import ItemOrdering

logger = logging.getLogger(__name__)


class WishServiceError(Exception):
    pass


class WishNotArchivableError(WishServiceError):
    pass


class WishNotUnarchivableError(WishServiceError):
    pass


class WishService:
    """Wish service: The Core’s wish service provides functions for handling
    wish model entities and wish-related business logic.
    """

    @staticmethod
    def get_wish(id: WishID) -> Wish:
        """Gets the wish with the matching id. Raises an `Wish.DoesNotExist`
        exception if a wish with the specified ID does not exist.

        Arguments:
            id: The wish’s identifier to look up.

        Returns:
            A wish entity.

        Raises:
            Wish.DoesNotExist
        """
        return Wish.objects.get(id_field=id)

    @staticmethod
    def query_wishes_for_wishlist(
        *,
        wishlist: Wishlist,
        archived: bool | None = None,
    ) -> QuerySet[Wish]:
        """Returns a lazy collection of wishes contained in the specified
        wish list.

        The collection of wishes is ordered by the wishlist’s setting.

        Arguments:
            wishlist: Wish list for the wishes to query for.
            archived: Designate to include or exclude archived wishes.

        Returns:
            Lazy collection of wishes.
        """
        queryset = Wish.objects.filter(wishlist=wishlist)
        if archived is not None:
            queryset = queryset.filter(archived=archived)
        queryset = queryset.select_related(Wish.Fields.WISHLIST)

        # ordering
        match wishlist.item_ordering:
            case ItemOrdering.NAME_ASCENDING:
                queryset = queryset.order_by(Wish.Fields.NAME)
            case ItemOrdering.NAME_DESCENDING:
                queryset = queryset.order_by(f"-{Wish.Fields.NAME}")
            case ItemOrdering.PREFERENCE_ASCENDING:
                queryset = queryset.order_by(Wish.Fields.PREFERENCE)
            case ItemOrdering.PREFERENCE_DESCENDING:
                queryset = queryset.order_by(f"-{Wish.Fields.PREFERENCE}")
            case ItemOrdering.CREATED_AT_ASCENDING:
                queryset = queryset.order_by(Wish.Fields.CREATED_AT)
            case ItemOrdering.CREATED_AT_DESCENDING:
                queryset = queryset.order_by(f"-{Wish.Fields.CREATED_AT}")
            case ItemOrdering.MODIFIED_AT_ASCENDING:
                queryset = queryset.order_by(Wish.Fields.MODIFIED_AT)
            case ItemOrdering.MODIFIED_AT_DESCENDING:
                queryset = queryset.order_by(f"-{Wish.Fields.MODIFIED_AT}")

        return queryset

    @staticmethod
    def archive(*, wish: Wish, save: bool = True) -> None:
        if wish.archivable:
            wish.archived = True
            wish.archived_at = timezone.now()
            if save:
                wish.save(update_fields=[Wish.Fields.ARCHIVED, Wish.Fields.ARCHIVED_AT])
        else:
            raise WishNotArchivableError()

    @staticmethod
    def unarchive(*, wish: Wish, save: bool = True) -> None:
        if wish.archived:
            wish.archived = False
            wish.archived_at = None
            if save:
                wish.save(update_fields=[Wish.Fields.ARCHIVED, Wish.Fields.ARCHIVED_AT])
        else:
            raise WishNotUnarchivableError()
