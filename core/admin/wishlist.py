"""Wishlist model representation in admin site."""
from django.contrib import admin

from core.models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Wishlist model representation in admin site."""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    Wishlist.Fields.ID,
                    Wishlist.Fields.NAME,
                    Wishlist.Fields.DESCRIPTION,
                    Wishlist.Fields.OWNER,
                    Wishlist.Fields.ITEM_ORDERING,
                    Wishlist.Fields.VISIBILITY,
                )
            },
        ),
        (
            "Options",
            {"fields": (Wishlist.Fields.MASK_RESERVATIONS,)},
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    Wishlist.Fields.CREATED_AT,
                    Wishlist.Fields.MODIFIED_AT,
                )
            },
        ),
    )

    readonly_fields = (
        Wishlist.Fields.ID,
        Wishlist.Fields.CREATED_AT,
        Wishlist.Fields.MODIFIED_AT,
    )

    list_display = (
        Wishlist.Fields.NAME,
        Wishlist.Fields.OWNER,
        Wishlist.Fields.DESCRIPTION,
        Wishlist.Fields.CREATED_AT,
    )

    list_filter = ()

    search_fields = [Wishlist.Fields.ID, Wishlist.Fields.NAME, Wishlist.Fields.DESCRIPTION]
