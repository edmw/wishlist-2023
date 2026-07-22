"""Reservation services."""

import logging

from django.utils import timezone

from core.models import Reservation, ReservationID
from core.models.reservation_lens import ReservationLens

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
        return ReservationLens.view().by_id(id=id).one()

    @staticmethod
    def complete(*, reservation: Reservation, save: bool = True) -> None:
        """Completes the specified reservation.

        Arguments:
            reservation: Reservation to complete.
            save: Flag, if the completed reservation should be saved.

        Raises:
            ReservationNotCompletableError: If the specified reservation can
                not be completed.
        """
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
