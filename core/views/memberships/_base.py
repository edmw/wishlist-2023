import logging
from typing import Any, Optional, Protocol, cast

from django.http import Http404, HttpRequest
from django.http.response import HttpResponseBase

from core import constants
from core.models import UserID, Wishlist, WishlistID
from core.services import PermissionService, WishlistService
from core.views._typing import HasModel, HasUser, HasWishlist

logger = logging.getLogger(__name__)


class IsMembershipView(HasUser, HasWishlist, HasModel, Protocol): ...


class HasPermissionForMembershipsViewMixin:
    """Verifies the requesting user is allowed to access a list’s memberships."""

    def dispatch(
        self: IsMembershipView,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseBase:
        """Dispatches the request after verifying owner-only membership access."""

        user = self.try_user()
        user_id = cast(Optional[UserID], kwargs.get(constants.USER_ID_KEY))
        wishlist_id = cast(Optional[WishlistID], kwargs.get(constants.LIST_ID_KEY))

        PermissionService.assert_user_object_by_id(
            requesting_user=user,
            user_object_id=user_id,
        )

        if not wishlist_id:
            PermissionService.assert_wishlist_object_by_id(
                requesting_user=user,
                wishlist_object_id=wishlist_id,
            )

        try:
            wishlist = WishlistService.get_wishlist(id=cast(WishlistID, wishlist_id))
        except Wishlist.DoesNotExist as wdne:
            # Preserve legacy behavior for unknown list IDs.
            PermissionService.assert_wishlist_object_by_id(
                requesting_user=user,
                wishlist_object_id=wishlist_id,
            )
            raise AssertionError("unreachable") from wdne

        if not user_id or wishlist.owner_id != user_id:
            logger.warning(
                "Inconsistent memberships URL: user_id does not match list owner.",
                extra={
                    "requesting.user": user,
                    "requested.user.id": user_id,
                    "requested.list.id": wishlist.id,
                    "requested.list.owner.id": wishlist.owner_id,
                },
            )
            raise Http404()

        PermissionService.assert_wishlist_object(
            requesting_user=user,
            wishlist_object=wishlist,
        )

        self.wishlist = wishlist
        return super().dispatch(request, *args, **kwargs)
