from __future__ import annotations

from typing import Self

from django.db.models import Count

from core.models._base import LensBase, LensHasOrderMixin
from core.models.user import User
from core.models.wishlist.wishlist import Wishlist


class WishlistLens(LensHasOrderMixin, LensBase[Wishlist]):
    model = Wishlist

    class ViewAlreadyNarrowedDownToOwnerError(LensBase.StateError):
        pass

    class ViewAlreadyPurgedOfListsError(LensBase.StateError):
        pass

    filter_for_owner: int | None = None
    exclude_for_lists: list[int] | None = None
    annotate_wishes_count: bool = False

    def by_owner(self, *, user: User) -> Self:
        """Narrows the view of this lens to all wish lists which are owned by
        the specified user. Raises if the view of this lens is already
        restricted by filtering on a specific owner.

        Arguments:
            user: User to whom the wish lists should belong.

        Returns:
            This lens with a view narrowed down to all wish lists which are
            owned by the specified user.

        Raises:
            WishlistLens.OwnerAlreadyQueriedError if the lens was already
            narrowed down to another user.
        """
        match self.filter_for_owner:
            case None:
                self.filter_for_owner = user.pk
                self.queryset = self.queryset.filter(owner=user)
                return self
            case _ if self.filter_for_owner == user.pk:
                return self
            case _:
                raise WishlistLens.ViewAlreadyNarrowedDownToOwnerError

    def without_lists(self, *, lists: list[Wishlist] | None) -> Self:
        """Narrows the view of this lens to all wish lists except the ones
        specified in the given list of wish list. Raises if the view of this
        lens is already restricted by excluding specific lists. Does nothing
        if no lists to exclude are specified.

        Arguments:
            lists: Wish lists to be excluded from the view of this lens.

        Returns:
            This lens with a view that omits the specified lists.

        Raises:
            WishlistLens.ListsAlreadyExcludedError if the lens is already
            omitting another set of wish lists.
        """
        if not lists:
            return self
        ids = [list.pk for list in lists]
        match self.exclude_for_lists:
            case None:
                self.exclude_for_lists = ids
                self.queryset = self.queryset.exclude(pk__in=ids)
                return self
            case _ if self.exclude_for_lists == ids:
                return self
            case _:
                raise WishlistLens.ViewAlreadyPurgedOfListsError

    def ordered_by_name(self) -> Self:
        """Orders the view of this lens by the wish list‘s names. Raises if
        there is already another order in effect.

        Returns:
            This lens with a view where the lists are ordered by their name.

        Raises:
            WishlistLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Wishlist.Fields.NAME)

    def last_created_first(self) -> Self:
        """Orders the view of this lens by the wish list‘s latest date of
        creation. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the lists are ordered by their
            date of creation.

        Raises:
            WishlistLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Wishlist.Fields.CREATED_AT)

    def last_modified_first(self) -> Self:
        """Orders the view of this lens by the wish list‘s latest date of
        modification. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the lists are ordered by their
            date of modification.

        Raises:
            WishlistLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Wishlist.Fields.MODIFIED_AT)

    def counting_wishes(self) -> Self:
        """Adds a count for all wishes per wish list to the view of this lens.

        Returns:
            This lens with a view where the lists have an attribute set with
            the count of their wishes.
        """
        match self.annotate_wishes_count:
            case False:
                self.annotate_wishes_count = True
                self.queryset = self.queryset.annotate(wishes_count=Count(Wishlist.Fields.WISHES))
                return self
            case _:
                return self

    def for_listing(self) -> Self:
        """Configures the view of this lens for listing the wish lists. They are
        ordered by their name and the wishes per list are counted.

        Returns:
            This lens with a view suitable for listing the wish lists.
        """
        return self.ordered_by_name().counting_wishes()
