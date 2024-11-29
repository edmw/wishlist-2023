import logging
from typing import Any, Optional, Protocol, cast

from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.views.generic.detail import SingleObjectMixin

from core import constants
from core.models import Reservation, UserID, WishID
from core.services import PermissionService, WishService
from core.views._typing import DoesViewDispatching, HasModel, HasRequest, HasUser

logger = logging.getLogger(__name__)


class IsReservationView(HasUser, HasModel, HasRequest, Protocol): ...


class HasPermissionForReservationViewMixin(DoesViewDispatching, SingleObjectMixin):
    """Verifies the requesting user is allowed to access the user’s reservations."""

    request: HttpRequest

    def dispatch(
        self: IsReservationView, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
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

        return super().dispatch(request, *args, **kwargs)

    def get_object(self: IsReservationView, queryset: QuerySet[Reservation] | None = None) -> Model:
        """Returns the reservation the view is displaying after verifying the
        requesting user is allowed to access the reservation.
        """
        # This is a sanity check while developing which can be safely removed in production.
        assert self.model == Reservation  # nosec

        # Get requested reservation from primary key in url.
        reservation_object = cast(Reservation, super().get_object(queryset))

        # Get authenticated user from request.
        user = self.try_user()

        # Assert requesting user has permission to access user object.
        return PermissionService.assert_reservation_object(
            requesting_user=user,
            reservation_object=reservation_object,
        )


class HasPermissionForReservationViewToCreateMixin(HasPermissionForReservationViewMixin):
    """Verifies the requesting user is allowed to create a reservation."""

    def dispatch(
        self: IsReservationView, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Dispatches the request to the supported http method handler after
        verifying the requesting user is allowed to access the requested
        resource.

        A user has permission to perform the query if the user identity in the
        request is entitled to access the list for the wish.
        """

        wish_id = WishID(self.request.GET[constants.ITEM_ID_KEY])
        wish = WishService.get_wish(id=wish_id)
        PermissionService.assert_reservation_for_wish(
            requesting_user=self.try_user(),
            wish=wish,
        )

        return super().dispatch(request, *args, **kwargs)
