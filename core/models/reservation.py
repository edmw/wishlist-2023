"""Model class representing a reservation for wishes."""
from __future__ import annotations

import logging

from django.conf import settings as django_settings
from django.db import models

from core.models import fields, types
from core.models._base import IDMixin

from .reservation_on_delete_notify import OnDeleteNotifyMixin
from .reservation_on_save_notify import OnSaveNotifyMixin

logger = logging.getLogger(__name__)


class Reservation(
    IDMixin[types.ReservationID],
    OnSaveNotifyMixin,
    OnDeleteNotifyMixin,
    models.Model,
):
    """Model used to represent a reservation persisted in database."""

    id_type = types.ReservationID
    id_field = fields.ReservationIDField()

    holder = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations"
    )
    holder_id: types.UserID

    wish = models.OneToOneField("Wish", on_delete=models.CASCADE, related_name="reservation")
    wish_id: types.WishID

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    completed = models.BooleanField(
        default=False,
        verbose_name="completed",
        help_text=(
            "Indicates whether this reservation can be revoked or whether the "
            "reservation should be considered complete."
        ),
    )
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta data for the Reservation model."""

        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "holder",
                    "wish",
                ],
                name="unique_reservation",
            )
        ]

    class Fields:
        """Field names for the Reservation model."""

        ID = "id_field"
        HOLDER = "holder"
        WISH = "wish"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"
        COMPLETED = "completed"
        COMPLETED_AT = "completed_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this reservation.

        Returns:
            Representation text.
        """
        return f"{self.holder_id} -> {self.wish_id}"

    def __repr__(self) -> str:
        """Returns a string reputation of this reservation.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}[{str(self.id)}]: holder={self.holder_id}; wish={self.wish}>"

    # Custom properties

    @property
    def is_completed(self) -> bool:
        # A reservation is completed if it is completed.
        return self.completed

    @property
    def undoable(self) -> bool:
        # A reservation can be undone if the reservation is not completed.
        return not self.is_completed

    @property
    def deletable(self) -> bool:
        # A reservation can be deleted anytime.
        return True
