import logging
from typing import Any, Optional, Protocol, cast

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from core import constants
from core.models import WishlistID
from core.services import PermissionService
from core.views._typing import HasModel, HasUser

logger = logging.getLogger(__name__)


class IsItemView(HasUser, HasModel, Protocol): ...


class HasPermissionForItemsViewMixin:
    """Verifies the requesting user is allowed to access the user’s items."""

    def dispatch(self: IsItemView, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Dispatches the request to the supported http method handler after
        verifying the requesting user is allowed to access the requested
        resource.

        A user has permission to perform the query if the requested list is
        editable by this user.
        """

        user = self.try_user()

        wishlist_id = cast(Optional[WishlistID], kwargs[constants.LIST_ID_KEY])
        PermissionService.assert_wishlist_editable_by_id(
            requesting_user=user,
            wishlist_object_id=wishlist_id,
        )

        return super().dispatch(request, *args, **kwargs)
