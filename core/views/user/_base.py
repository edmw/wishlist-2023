import logging
from typing import Protocol, cast

from django.db.models import Model, QuerySet
from django.views.generic.detail import SingleObjectMixin

from core.models import User
from core.services import PermissionService, UserSettingsService
from core.views._typing import HasModel, HasUser

logger = logging.getLogger(__name__)


class IsUserView(HasUser, HasModel, Protocol):
    ...


class HasPermissionForUserViewMixin(SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s data."""

    def get_object(self: IsUserView, queryset: QuerySet[User] | None = None) -> Model:
        """Returns the view object after verifying the requesting user is
        allowed to access the object.

        A user has permission to access the user data if it is their own data.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == User  # nosec

        user_object = cast(User, super().get_object(queryset))
        return PermissionService.assert_user_object(
            requesting_user=self.try_user(),
            user_object=user_object,
        )


class NeedsSettingsForUserViewMixin(SingleObjectMixin):
    """Ensures the requested user has had their settings set up."""

    def get_object(self: IsUserView, queryset: QuerySet[User] | None = None) -> Model:
        """Returns the view object after making sure that the requested user
        has set up their settings.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == User  # nosec

        user_object = cast(User, super().get_object(queryset))
        UserSettingsService.settings_for(user=user_object)
        return user_object
