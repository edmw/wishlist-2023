import logging
from typing import Protocol, cast

from django.db.models import Model, QuerySet
from django.views.generic.detail import SingleObjectMixin

from core.models import Wishlist
from core.services import PermissionService
from core.views._typing import HasModel, HasUser
from core.views.lists._base import HasPermissionForListsViewMixin

logger = logging.getLogger(__name__)


class IsListView(HasUser, HasModel, Protocol):
    ...


class HasPermissionForListViewMixin(HasPermissionForListsViewMixin, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s lists."""

    def get_object(self: IsListView, queryset: QuerySet[Wishlist] | None = None) -> Model:
        """Returns the view object after verifying the requesting user is
        allowed to access the object.

        A user has permission to access the wish list if the list is owned by
        this user.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == Wishlist  # nosec

        list_object = cast(Wishlist, super().get_object(queryset))
        return PermissionService.assert_wishlist_object(
            requesting_user=self.try_user(),
            wishlist_object=list_object,
        )
