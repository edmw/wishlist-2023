import logging
from typing import Any, Optional, Protocol, cast

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from core import constants
from core.models import UserID, WishlistID
from core.services import PermissionService
from core.views._typing import DoesViewDispatching, HasModel, HasUser

logger = logging.getLogger(__name__)


class IsItemView(HasUser, HasModel, Protocol): ...


class HasPermissionForItemsViewMixin(DoesViewDispatching):
    """Verifies the requesting user is allowed to access the user’s items."""

    def dispatch(self: IsItemView, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Dispatches the request to the supported http method handler after
        verifying the requesting user is allowed to access the requested
        resource.

        A user has permission to perform the query if the user identity in the
        request is their own and if the requested list is owned by this user.
        """

        user = self.try_user()

        user_id = cast(Optional[UserID], kwargs.get(constants.USER_ID_KEY))
        PermissionService.assert_user_object_by_id(
            requesting_user=user,
            user_object_id=user_id,
        )

        wishlist_id = cast(Optional[WishlistID], kwargs[constants.LIST_ID_KEY])
        PermissionService.assert_wishlist_object_by_id(
            requesting_user=user,
            wishlist_object_id=wishlist_id,
        )

        return super().dispatch(request, *args, **kwargs)
