from django.db import models

from ._uuid import UUIDFieldMixin


class ReservationIDField(UUIDFieldMixin, models.UUIDField):
    """Model field describing a reservation’s identifier."""

    description = "Unique ID of a reservation"
