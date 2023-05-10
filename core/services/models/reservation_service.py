"""Reservation services."""

import logging

from django.db.models import QuerySet
from django.utils import timezone

from core.models import Reservation, ReservationID, User

logger = logging.getLogger(__name__)


class ReservationServiceError(Exception):
    pass


class ReservationNotCompletableError(ReservationServiceError):
    pass


class ReservationService:
    """Reservation service: The Core’s reservation service provides functions
    for handling reservation model entities and reservation-related business
    logic.
    """

    @staticmethod
    def get_reservation(id: ReservationID) -> Reservation:
        """Gets the reservation with the matching id. Raises an
        `Reservation.DoesNotExist` exception if a reservation with the specified
        ID does not exist.

        Arguments:
            id: The reservation identifier to look up.

        Returns:
            A reservation entity.

        Raises:
            Reservation.DoesNotExist
        """
        return Reservation.objects.get(id_field=id)

    @staticmethod
    def query_reservations_for_user(*, user: User) -> QuerySet[Reservation]:
        """Returns a lazy collection of reservations whose user is the specified
        user.

        Arguments:
            user: User of the reservations to query for.

        Returns:
            Lazy collection of reservations.
        """
        return Reservation.objects.filter(holder=user)

    @staticmethod
    def complete(*, reservation: Reservation, save: bool = True) -> None:
        if not reservation.completed:
            reservation.completed = True
            reservation.completed_at = timezone.now()
            if save:
                reservation.save(
                    update_fields=[
                        Reservation.Fields.COMPLETED,
                        Reservation.Fields.COMPLETED_AT,
                    ]
                )
        else:
            raise ReservationNotCompletableError()
