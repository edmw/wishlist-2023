"""Reservation model representation in admin site."""
from django.contrib import admin

from core.models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Reservation model representation in admin site."""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    Reservation.Fields.ID,
                    Reservation.Fields.HOLDER,
                    Reservation.Fields.WISH,
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    Reservation.Fields.CREATED_AT,
                    Reservation.Fields.MODIFIED_AT,
                    Reservation.Fields.COMPLETED,
                    Reservation.Fields.COMPLETED_AT,
                )
            },
        ),
    )

    readonly_fields = (
        Reservation.Fields.ID,
        Reservation.Fields.CREATED_AT,
        Reservation.Fields.MODIFIED_AT,
    )

    list_display = (
        Reservation.Fields.HOLDER,
        Reservation.Fields.WISH,
        Reservation.Fields.CREATED_AT,
    )

    search_fields = [Reservation.Fields.ID]
