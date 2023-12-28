from __future__ import annotations

from typing import Self

from core.models._base import LensBase, LensHasOrderMixin
from core.models.types import ItemOrdering
from core.models.wish import Wish
from core.models.wishlist import Wishlist


class WishLens(LensHasOrderMixin, LensBase[Wish]):
    model = Wish

    class ViewAlreadyNarrowedDownToListError(LensBase.StateError):
        pass

    filter_for_wishlist: int | None = None
    filter_for_archived: bool | None = None
    order_by: str | None = None

    def by_wishlist(self, *, list: Wishlist) -> Self:
        """Narrows the view of this lens to all wishes which are on the
        specified wish list. Orders the view of the wishes by the ordering
        configured for the specified wish list. Raises if the view of this lens
        is already restricted by filtering on a specific list.

        Arguments:
            wishlist: Wish list the wishes should belong to.

        Returns:
            This lens with a view narrowed down to all wishes which are on
            the specified wish list.

        Raises:
            WishLens.ListAlreadyQueriedError if the lens was already
            narrowed down to another list.
        """
        match self.filter_for_wishlist:
            case None:
                self.filter_for_wishlist = list.pk
                self.queryset = self.queryset.filter(wishlist=list)
                # ordering
                match list.item_ordering:
                    case ItemOrdering.NAME_ASCENDING:
                        field = Wish.Fields.NAME
                    case ItemOrdering.NAME_DESCENDING:
                        field = f"-{Wish.Fields.NAME}"
                    case ItemOrdering.PREFERENCE_ASCENDING:
                        field = Wish.Fields.PREFERENCE
                    case ItemOrdering.PREFERENCE_DESCENDING:
                        field = f"-{Wish.Fields.PREFERENCE}"
                    case ItemOrdering.CREATED_AT_ASCENDING:
                        field = Wish.Fields.CREATED_AT
                    case ItemOrdering.CREATED_AT_DESCENDING:
                        field = f"-{Wish.Fields.CREATED_AT}"
                    case ItemOrdering.MODIFIED_AT_ASCENDING:
                        field = Wish.Fields.MODIFIED_AT
                    case ItemOrdering.MODIFIED_AT_DESCENDING:
                        field = f"-{Wish.Fields.MODIFIED_AT}"
                    case _:
                        field = Wish.Fields.NAME
                return self.ordered_by(field)
            case _ if self.filter_for_wishlist == list.pk:
                return self
            case _:
                raise WishLens.ViewAlreadyNarrowedDownToListError

    def without_archived(self) -> Self:
        """Restricts the view of this lens to wishes which are not archived
        yet. Raises if there is already another setting in effect.

        Returns:
            This lens with a view restricted to wishes which are not archived
            yet.

        Raises:
            WishLens.StateError if there is already another setting in
            effect.
        """
        match self.filter_for_archived:
            case None:
                self.filter_for_archived = False
                self.queryset = self.queryset.filter(archived=False)
                return self
            case _ if self.filter_for_archived is False:
                return self
            case _:
                raise WishLens.StateError

    def last_created_first(self) -> Self:
        """Orders the view of this lens by the wishes‘ latest date of
        creation. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the wishes are ordered by their
            date of creation.

        Raises:
            WishLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Wish.Fields.CREATED_AT)

    def last_modified_first(self) -> Self:
        """Orders the view of this lens by the wishes‘ latest date of
        modification. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the wishes are ordered by their
            date of modification.

        Raises:
            WishLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Wish.Fields.MODIFIED_AT)

    def for_listing(self) -> Self:
        """Configures the view of this lens for listing the wishes. Fetches
        the related wish lists.

        Returns:
            This lens with a view suitable for listing the wish lists.
        """
        self.queryset = self.queryset.select_related(Wish.Fields.WISHLIST)

        return self
