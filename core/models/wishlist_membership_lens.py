from __future__ import annotations

from typing import Self

from core.models._base import LensBase
from core.models.types import WishlistMembershipRole
from core.models.user import User
from core.models.wishlist import Wishlist
from core.models.wishlist_membership import WishlistMembership


class WishlistMembershipLens(LensBase[WishlistMembership]):
    model = WishlistMembership

    class ViewAlreadyNarrowedDownToWishlistError(LensBase.StateError):
        pass

    class ViewAlreadyNarrowedDownToUserError(LensBase.StateError):
        pass

    filter_for_wishlist: int | None = None
    filter_for_user: int | None = None
    filter_for_editors: bool = False

    def by_wishlist(self, *, wishlist: Wishlist) -> Self:
        match self.filter_for_wishlist:
            case None:
                self.filter_for_wishlist = wishlist.pk
                self.queryset = self.queryset.filter(wishlist=wishlist)
                return self
            case _ if self.filter_for_wishlist == wishlist.pk:
                return self
            case _:
                raise WishlistMembershipLens.ViewAlreadyNarrowedDownToWishlistError

    def by_user(self, *, user: User) -> Self:
        match self.filter_for_user:
            case None:
                self.filter_for_user = user.pk
                self.queryset = self.queryset.filter(user=user)
                return self
            case _ if self.filter_for_user == user.pk:
                return self
            case _:
                raise WishlistMembershipLens.ViewAlreadyNarrowedDownToUserError

    def editors_only(self) -> Self:
        if self.filter_for_editors:
            return self

        self.filter_for_editors = True
        self.queryset = self.queryset.filter(role_field=WishlistMembershipRole.EDITOR)
        return self
