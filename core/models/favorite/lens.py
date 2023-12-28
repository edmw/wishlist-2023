from __future__ import annotations

from django.db.models import Prefetch

from core.models._base import LensBase, LensHasOrderMixin
from core.models.favorite.favorite import Favorite
from core.models.user import User
from core.models.wishlist.lens import WishlistLens
from core.models.wishlist.wishlist import Wishlist


class FavoriteLens(LensHasOrderMixin, LensBase[Favorite]):
    model = Favorite

    class ViewAlreadyNarrowedDownToUserError(LensBase.StateError):
        pass

    class ViewAlreadyNarrowedDownToListError(LensBase.StateError):
        pass

    filter_for_user: int | None = None
    filter_for_wishlist: int | None = None
    order_by: str | None = None

    def by_user(self, *, user: User) -> FavoriteLens:
        """Narrows the view of this lens to all favorites which are owned by
        the specified user. Raises if the view of this lens is already
        restricted by filtering on a specific owner.

        Arguments:
            user: User to whom the favorites should belong.

        Returns:
            This lens with a view narrowed down to all favorites which are
            owned by the specified user.

        Raises:
            FavoriteLens.OwnerAlreadyQueriedError if the lens was already
            narrowed down to another user.
        """
        match self.filter_for_user:
            case None:
                self.filter_for_user = user.pk
                self.queryset = self.queryset.filter(user=user)
                return self
            case _ if self.filter_for_user == user.pk:
                return self
            case _:
                raise FavoriteLens.ViewAlreadyNarrowedDownToUserError

    def by_wishlist(self, *, wishlist: Wishlist) -> FavoriteLens:
        """Narrows the view of this lens to all favorites which are set for
        the specified wish list. Raises if the view of this lens is already
        restricted by filtering on a specific list.

        Arguments:
            wishlist: Wish list the favorites should be set for.

        Returns:
            This lens with a view narrowed down to all favorites which are set
            for the specified wish list.

        Raises:
            FavoriteLens.ListAlreadyQueriedError if the lens was already
            narrowed down to another list.
        """
        match self.filter_for_wishlist:
            case None:
                self.filter_for_wishlist = wishlist.pk
                self.queryset = self.queryset.filter(wishlist=wishlist)
                return self
            case _ if self.filter_for_wishlist == wishlist.pk:
                return self
            case _:
                raise FavoriteLens.ViewAlreadyNarrowedDownToListError

    def ordered_by_wishlist_name(self) -> FavoriteLens:
        """Orders the view of this lens by the favorite‘s wish list names.
        Raises if there is already another order in effect.

        Returns:
            This lens with a view where the favorites are ordered by the name
            of their wish list.

        Raises:
            FavoriteLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field="wishlist__name_field")

    def last_created_first(self) -> FavoriteLens:
        """Orders the view of this lens by the favorite‘s latest date of
        creation. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the favorites are ordered by their
            date of creation.

        Raises:
            FavoriteLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Favorite.Fields.CREATED_AT)

    def last_modified_first(self) -> FavoriteLens:
        """Orders the view of this lens by the favorite‘s latest date of
        modification. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the favorites are ordered by their
            date of modification.

        Raises:
            FavoriteLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Favorite.Fields.MODIFIED_AT)

    def for_iterating(self) -> FavoriteLens:
        """Configures the view of this lens for iterating the favorites. When
        the view is narrowed down by a user, fetches the related wishlists.
        When the view is narrowed down by a wishlist, fetches the related
        users.

        Returns:
            This lens with a view suitable for iterating the favorites.
        """
        if not self.filter_for_user:
            self.queryset = self.queryset.select_related(Favorite.Fields.USER)
        if not self.filter_for_wishlist:
            self.queryset = self.queryset.select_related(Favorite.Fields.WISHLIST)

        return self

    def for_listing(self) -> FavoriteLens:
        """Configures the view of this lens for listing the favorites. They are
        ordered by the name of their wish list. Fetches the related wish lists
        while counting their wishes.

        Returns:
            This lens with a view suitable for listing the favorites.
        """
        self.queryset = self.queryset.prefetch_related(
            Prefetch(
                Favorite.Fields.WISHLIST,
                queryset=WishlistLens.view().counting_wishes().queryset,
            )
        )
        return self.ordered_by_wishlist_name()
