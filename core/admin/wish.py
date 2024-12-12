"""Wish model representation in admin site."""

from typing import Iterable

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from core.models import Reservation, Wish

RESERVED_FIELD = "reserved"


class WishReservationInline(admin.StackedInline):
    """Reservation model representation inside Wish model representation."""

    model = Reservation
    fk_name = Reservation.Fields.WISH
    can_delete = False
    view_on_site = False


class WishReservationFilter(admin.SimpleListFilter):
    """Filter for Wish model representations in respect of the wish’s
    reservation status.
    """

    title = RESERVED_FIELD
    parameter_name = RESERVED_FIELD

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> Iterable[tuple[str, str]]:
        """Returns possible options for this filter.

        Arguments:
            request: HTTP Request.
            model_admin: Admin model to which apply this filter to.

        Returns:
            List of tuples with value and label for each filter option.
        """
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[Wish],
    ) -> QuerySet[Wish]:
        """Returns a filtered queryset according to the filter’s setting value.

        Arguments:
            request: HTTP Request.
            queryset: Queryset to be filtered.

        Returns:
            Filtered queryset.
        """
        value = self.value()
        if value == "yes":
            # apply filter to show only reserved wishes.
            return queryset.filter(reservation__isnull=False)
        elif value == "no":
            # apply filter to show only wishes not reserved yet.
            return queryset.filter(reservation__isnull=True)
        return queryset


@admin.register(Wish)
class WishAdmin(admin.ModelAdmin):
    """Wish model representation in admin site."""

    inlines = [
        WishReservationInline,
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    Wish.Fields.ID,
                    Wish.Fields.NAME,
                    Wish.Fields.DESCRIPTION,
                    Wish.Fields.REFERENCE,
                    Wish.Fields.REFERENCE_PHOTO,
                    Wish.Fields.PREFERENCE,
                    Wish.Fields.WISHLIST,
                )
            },
        ),
        (
            "Image",
            {
                "fields": (
                    Wish.Fields.IMAGE,
                    "image_preview",
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    Wish.Fields.CREATED_AT,
                    Wish.Fields.MODIFIED_AT,
                    Wish.Fields.ARCHIVED,
                    Wish.Fields.ARCHIVED_AT,
                )
            },
        ),
    )

    readonly_fields = (
        Wish.Fields.ID,
        Wish.Fields.CREATED_AT,
        Wish.Fields.MODIFIED_AT,
        Wish.Fields.IMAGE,
        "image_preview",
        RESERVED_FIELD,
    )

    list_display = (
        Wish.Fields.NAME,
        Wish.Fields.WISHLIST,
        Wish.Fields.DESCRIPTION,
        RESERVED_FIELD,
        Wish.Fields.ARCHIVED,
        Wish.Fields.CREATED_AT,
    )

    list_filter = (
        (Wish.Fields.ARCHIVED, admin.BooleanFieldListFilter),
        WishReservationFilter,
    )

    search_fields = [Wish.Fields.ID, Wish.Fields.NAME, Wish.Fields.DESCRIPTION]

    def reserved(self, wish: Wish) -> bool:
        """Returns True if the specified wish is reserved, false otherwise.

        Used to display a on/off icon in admin user interface.

        Arguments:
            wish: The wish.

        Returns:
            True, if wish is reserved, false otherwise.
        """
        return wish.is_reserved

    reserved.boolean = True
    reserved.admin_order_field = "reservation"

    def image_preview(self, wish: Wish) -> SafeString:
        """Returns HTML used for displaying the preview image of the wish’s
        photo.

        Arguments:
            wish: The wish.

        Returns:
            HTML (safe).
        """
        # SECURITY: Image url is safe (internal).
        return mark_safe(  # nosec
            '<img src="{url}" width="256" height="256" />'.format(url=wish.image_field.url)
        )
