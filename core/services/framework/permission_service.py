import copy
import logging
from typing import Any

from django.core.exceptions import PermissionDenied

from core.models import (
    Favorite,
    FavoriteID,
    Reservation,
    ReservationID,
    User,
    UserID,
    Wish,
    WishID,
    Wishlist,
    WishlistID,
)
from core.models.types import Visibility
from core.services.models import (
    FavoriteService,
    ReservationService,
    UserService,
    WishlistService,
    WishService,
)

logger = logging.getLogger(__name__)


def _log_critical(
    message: str,
    requesting: User,
    requested: User
    | UserID
    | Wishlist
    | WishlistID
    | Wish
    | WishID
    | Favorite
    | FavoriteID
    | Reservation
    | ReservationID
    | None = None,
) -> None:
    # Because request user may be wrapped in a proxy object,
    # make a copy which will return the actual user instance.
    # This will make the log message much nicer.
    requesting = copy.copy(requesting)

    extra: dict[str, Any] = {"requesting.user": requesting}
    match requested:
        case User() | Wishlist() | Wish() | Favorite() | Reservation():
            extra = {
                **extra,
                "requested.resource": requested,
                "requested.resource.id": requested.id,
            }
        case UserID() | WishlistID() | WishID() | FavoriteID() | ReservationID():
            extra = {
                **extra,
                "requested.resource": requested,
                "requested.resource.id": requested,
            }
    logger.critical(f"PermissionDenied: {message}", extra=extra)


class PermissionService:
    @staticmethod
    def assert_user_object(*, requesting_user: User, user_object: User) -> User:
        if requesting_user == user_object:
            return user_object

        else:
            _log_critical(
                "Authenticated user requesting other user’s data.",
                requesting_user,
                user_object,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_user_object_by_id(*, requesting_user: User, user_object_id: UserID | None) -> User:
        if not user_object_id:
            _log_critical(
                "Authenticated user requesting no user’s data.",
                requesting_user,
            )
            raise PermissionDenied()

        try:
            user_object = UserService.get_user(id=user_object_id)

            # Assert requesting user has permission to access user object.
            return PermissionService.assert_user_object(
                requesting_user=requesting_user,
                user_object=user_object,
            )
        except User.DoesNotExist as udne:
            _log_critical(
                "Authenticated user requesting unknown user’s data.",
                requesting_user,
                user_object_id,
            )
            raise PermissionDenied() from udne

    @staticmethod
    def assert_wishlist_object(*, requesting_user: User, wishlist_object: Wishlist) -> Wishlist:
        # Requesting user must match the list’s owner!
        if requesting_user == wishlist_object.owner:
            return wishlist_object

        else:
            _log_critical(
                "Authenticated user requesting other user’s lists.",
                requesting_user,
                wishlist_object,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_wishlist_object_by_id(
        *, requesting_user: User, wishlist_object_id: WishlistID | None
    ) -> Wishlist:
        if not wishlist_object_id:
            _log_critical(
                "Authenticated user requesting no list.",
                requesting_user,
            )
            raise PermissionDenied()

        try:
            list_object = WishlistService.get_wishlist(id=wishlist_object_id)

            # Assert requesting user has permission to access list object.
            return PermissionService.assert_wishlist_object(
                requesting_user=requesting_user,
                wishlist_object=list_object,
            )
        except Wishlist.DoesNotExist as wdne:
            _log_critical(
                "Authenticated user requesting unknown list.",
                requesting_user,
                wishlist_object_id,
            )
            raise PermissionDenied() from wdne

    @staticmethod
    def assert_wish_object(*, requesting_user: User, wish_object: Wish) -> Wish:
        # Requesting user must match the item’s list owner!
        if requesting_user == wish_object.wishlist.owner:
            return wish_object

        else:
            _log_critical(
                "Authenticated user requesting other user’s items.",
                requesting_user,
                wish_object,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_wish_object_by_id(*, requesting_user: User, wish_object_id: WishID | None) -> Wish:
        if not wish_object_id:
            _log_critical(
                "Authenticated user requesting no item.",
                requesting_user,
            )
            raise PermissionDenied()

        try:
            item_object = WishService.get_wish(id=wish_object_id)

            # Assert requesting user has permission to access item object.
            return PermissionService.assert_wish_object(
                requesting_user=requesting_user,
                wish_object=item_object,
            )
        except Wish.DoesNotExist as wdne:
            _log_critical(
                "Authenticated user requesting unknown item.",
                requesting_user,
                wish_object_id,
            )
            raise PermissionDenied() from wdne

    @staticmethod
    def assert_favorite_object(*, requesting_user: User, favorite_object: Favorite) -> Favorite:
        # Requesting user must match the favorite’s user!
        if requesting_user == favorite_object.user:
            return favorite_object

        else:
            _log_critical(
                "Authenticated user requesting other user’s favorites.",
                requesting_user,
                favorite_object,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_favorite_object_by_id(
        *, requesting_user: User, favorite_object_id: FavoriteID | None
    ) -> Favorite:
        if not favorite_object_id:
            _log_critical(
                "Authenticated user requesting no favorite.",
                requesting_user,
            )
            raise PermissionDenied()

        try:
            favorite_object = FavoriteService.get_favorite(id=favorite_object_id)

            # Assert requesting user has permission to access favorite object.
            return PermissionService.assert_favorite_object(
                requesting_user=requesting_user,
                favorite_object=favorite_object,
            )
        except Wishlist.DoesNotExist as wdne:
            _log_critical(
                "Authenticated user requesting unknown list.",
                requesting_user,
                favorite_object_id,
            )
            raise PermissionDenied() from wdne

    @staticmethod
    def assert_wishlist(*, requesting_user: User, wishlist: Wishlist) -> Wishlist:
        if requesting_user == wishlist.owner or (
            wishlist.visibility == Visibility.USERS or wishlist.visibility == Visibility.PUBLIC
        ):
            return wishlist

        else:
            _log_critical(
                "Authenticated user requesting wishlist without permission.",
                requesting_user,
                wishlist,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_reservation_object(*, requesting_user: User, reservation_object: Reservation) -> Reservation:
        # Requesting user must match the reservation’s holder!
        if requesting_user == reservation_object.holder:
            return reservation_object

        else:
            _log_critical(
                "Authenticated user requesting other user’s reservations.",
                requesting_user,
                reservation_object,
            )
            raise PermissionDenied()

    @staticmethod
    def assert_reservation_object_by_id(
        *, requesting_user: User, reservation_object_id: ReservationID | None
    ) -> Reservation:
        if not reservation_object_id:
            _log_critical(
                "Authenticated user requesting no reservation.",
                requesting_user,
            )
            raise PermissionDenied()

        try:
            reservation_object = ReservationService.get_reservation(id=reservation_object_id)

            # Assert requesting user has permission to access reservation object.
            return PermissionService.assert_reservation_object(
                requesting_user=requesting_user,
                reservation_object=reservation_object,
            )
        except Wishlist.DoesNotExist as wdne:
            _log_critical(
                "Authenticated user requesting unknown reservation.",
                requesting_user,
                reservation_object_id,
            )
            raise PermissionDenied() from wdne

    @staticmethod
    def assert_reservation_for_wish(*, requesting_user: User, wish: Wish) -> None:
        PermissionService.assert_wishlist(requesting_user=requesting_user, wishlist=wish.wishlist)
