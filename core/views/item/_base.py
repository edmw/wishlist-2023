import logging
from typing import Protocol, cast

from django.db.models import Model, QuerySet
from django.views.generic.detail import SingleObjectMixin

from core.models import Wish
from core.services import PermissionService
from core.views._typing import HasModel, HasUser
from core.views.items._base import HasPermissionForItemsViewMixin

logger = logging.getLogger(__name__)


class IsItemView(HasUser, HasModel, Protocol):
    ...


class HasPermissionForItemViewMixin(HasPermissionForItemsViewMixin, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s items."""

    def get_object(self: IsItemView, queryset: QuerySet[Wish] | None = None) -> Model:
        """Returns the view object after verifying the requesting user is
        allowed to access the object.

        A user has permission to access the wish if the wish is on a list which
        is owned by this user.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == Wish  # nosec

        item_object = cast(Wish, super().get_object(queryset))
        return PermissionService.assert_wish_object(
            requesting_user=self.try_user(),
            wish_object=item_object,
        )
