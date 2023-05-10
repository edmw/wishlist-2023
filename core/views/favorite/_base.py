import logging
from typing import cast

from django.db.models import Model, QuerySet
from django.views.generic.detail import SingleObjectMixin

from core.models import Favorite
from core.services import PermissionService
from core.views.favorites._base import (
    HasPermissionForFavoritesViewMixin,
    IsFavoriteView,
)

logger = logging.getLogger(__name__)


class HasPermissionForFavoriteViewMixin(HasPermissionForFavoritesViewMixin, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s favorites."""

    def get_object(self: IsFavoriteView, queryset: QuerySet[Favorite] | None = None) -> Model:
        """Returns the view object after verifying the requesting user is
        allowed to access the object.

        A user has permission to access the favorite if the favorite belongs to
        them.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == Favorite  # nosec

        favorite_object = cast(Favorite, super().get_object(queryset))
        return PermissionService.assert_favorite_object(
            requesting_user=self.try_user(),
            favorite_object=favorite_object,
        )
