import logging
from typing import Any, Optional, Protocol, cast

from django.http import HttpRequest
from django.http.response import HttpResponseBase

from core import constants
from core.models import UserID
from core.services import PermissionService
from core.views._typing import DoesViewDispatching, HasModel, HasUser

logger = logging.getLogger(__name__)


class IsListView(HasUser, HasModel, Protocol): ...


class HasPermissionForListsViewMixin:
    """Verifies the requesting user is allowed to access the user’s lists."""

    def dispatch(self: IsListView, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Dispatches the request to the supported http method handler after
        verifying the requesting user is allowed to access the requested
        resource.

        A user has permission to perform the query if the user identity in the
        request is their own.
        """
        user_id = cast(Optional[UserID], kwargs.get(constants.USER_ID_KEY))
        PermissionService.assert_user_object_by_id(
            requesting_user=self.try_user(),
            user_object_id=user_id,
        )
        return cast(DoesViewDispatching, super()).dispatch(request, *args, **kwargs)
