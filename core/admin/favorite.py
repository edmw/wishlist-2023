"""Favorite model representation in admin site."""
from django.contrib import admin

from core.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Favorite model representation in admin site."""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    Favorite.Fields.ID,
                    Favorite.Fields.USER,
                    Favorite.Fields.WISHLIST,
                )
            },
        ),
        (
            "Options",
            {"fields": (Favorite.Fields.NOTIFY_ON_ITEM_CREATE,)},
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    Favorite.Fields.CREATED_AT,
                    Favorite.Fields.MODIFIED_AT,
                )
            },
        ),
    )

    readonly_fields = (
        Favorite.Fields.ID,
        Favorite.Fields.CREATED_AT,
        Favorite.Fields.MODIFIED_AT,
    )

    list_display = (
        Favorite.Fields.USER,
        Favorite.Fields.WISHLIST,
        Favorite.Fields.CREATED_AT,
    )

    search_fields = [Favorite.Fields.ID]
