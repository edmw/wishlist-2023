import logging
from typing import Protocol, cast

from django.db.models import QuerySet
from django.views.generic.detail import SingleObjectMixin

from core.models import Wish
from core.services import PermissionService
from core.views._typing import HasModel, HasUser
from core.views.items._base import HasPermissionForItemsViewMixin

logger = logging.getLogger(__name__)


class IsItemView(HasUser, HasModel, Protocol):
    def get_item(self, queryset: QuerySet[Wish] | None = None) -> Wish: ...

    def get_permitted_item(self, queryset: QuerySet[Wish] | None = None) -> Wish: ...


class PermittedForItemViewMixin(HasPermissionForItemsViewMixin):
    """Provides wish-based permission checks for item-related views."""

    def get_item(self: IsItemView, queryset: QuerySet[Wish] | None = None) -> Wish:
        raise NotImplementedError

    def get_permitted_item(self: IsItemView, queryset: QuerySet[Wish] | None = None) -> Wish:
        """Returns the permission-checked item for this request."""
        item = self.get_item(queryset)
        return PermissionService.assert_wish_object(
            requesting_user=self.try_user(),
            wish_object=item,
        )


class HasPermissionForItemViewMixin(PermittedForItemViewMixin, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s items."""

    def get_item(self: IsItemView, queryset: QuerySet[Wish] | None = None) -> Wish:
        """Returns the requested item instance."""
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == Wish  # nosec

        return cast(Wish, super().get_object(queryset))

    def get_object(self: IsItemView, queryset: QuerySet[Wish] | None = None) -> Wish:
        """Returns the view object after verifying the requesting user is
        allowed to access the object.

        A user has permission to access the wish if the wish is on a list which
        is owned by this user.
        """
        return self.get_permitted_item(queryset)
