from __future__ import annotations

from core.models._base import LensBase, LensHasIdMixin, LensHasOrderMixin
from core.models.reservation import Reservation
from core.models.user import User


class ReservationLens(LensHasIdMixin, LensHasOrderMixin, LensBase[Reservation]):
    model = Reservation

    class ViewAlreadyNarrowedDownToHolderError(LensBase.StateError):
        pass

    filter_for_user: int | None = None
    order_by: str | None = None

    def by_holder(self, *, user: User) -> ReservationLens:
        """Narrows the view of this lens to all reservations which are hold
        by the specified user. Raises if the view of this lens is already
        restricted by filtering on a specific owner.

        Arguments:
            user: User to whom the reservations should belong.

        Returns:
            This lens with a view narrowed down to all reservations which are
            hold by the specified user.

        Raises:
            ReservationLens.OwnerAlreadyQueriedError if the lens was already
            narrowed down to another user.
        """
        self._assert_not_consumed()
        match self.filter_for_user:
            case None:
                self.filter_for_user = user.pk
                self.queryset = self.queryset.filter(holder=user)
                return self
            case _ if self.filter_for_user == user.pk:
                return self
            case _:
                raise ReservationLens.ViewAlreadyNarrowedDownToHolderError

    def ordered_by_wish_name(self) -> ReservationLens:
        """Orders the view of this lens by the reservation‘s wish names.
        Raises if there is already another order in effect.

        Returns:
            This lens with a view where the reservations are ordered by the
            name of their wish.

        Raises:
            ReservationLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field="wish__name_field")

    def last_created_first(self) -> ReservationLens:
        """Orders the view of this lens by the reservation‘s latest date of
        creation. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the reservations are ordered by their
            date of creation.

        Raises:
            ReservationLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Reservation.Fields.CREATED_AT)

    def last_modified_first(self) -> ReservationLens:
        """Orders the view of this lens by the reservation‘s latest date of
        modification. Raises if there is already another order in effect.

        Returns:
            This lens with a view where the reservations are ordered by their
            date of modification.

        Raises:
            ReservationLens.OrderAlreadySetError if there is already another
            ordering in effect.
        """
        return self.ordered_by(field=Reservation.Fields.MODIFIED_AT)
