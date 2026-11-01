"""Wishlist invitation model representation in admin site."""

from django.contrib import admin

from core.models import WishlistInvitation


@admin.register(WishlistInvitation)
class WishlistInvitationAdmin(admin.ModelAdmin):
    """Wishlist invitation model representation in admin site."""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    WishlistInvitation.Fields.ID,
                    WishlistInvitation.Fields.WISHLIST,
                    WishlistInvitation.Fields.INVITER,
                    WishlistInvitation.Fields.INVITEE_EMAIL,
                    WishlistInvitation.Fields.CODE,
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    WishlistInvitation.Fields.CREATED_AT,
                    WishlistInvitation.Fields.SENT,
                    WishlistInvitation.Fields.SENT_AT,
                    WishlistInvitation.Fields.ACCEPTED,
                    WishlistInvitation.Fields.ACCEPTED_AT,
                )
            },
        ),
    )

    readonly_fields = (
        WishlistInvitation.Fields.ID,
        WishlistInvitation.Fields.CODE,
        WishlistInvitation.Fields.CREATED_AT,
        WishlistInvitation.Fields.SENT_AT,
        WishlistInvitation.Fields.ACCEPTED_AT,
    )

    list_display = (
        WishlistInvitation.Fields.WISHLIST,
        WishlistInvitation.Fields.INVITER,
        WishlistInvitation.Fields.INVITEE_EMAIL,
        WishlistInvitation.Fields.CREATED_AT,
        WishlistInvitation.Fields.SENT,
        WishlistInvitation.Fields.ACCEPTED,
    )

    list_filter = (WishlistInvitation.Fields.SENT, WishlistInvitation.Fields.ACCEPTED)

    search_fields = [
        WishlistInvitation.Fields.ID,
        WishlistInvitation.Fields.CODE,
        WishlistInvitation.Fields.INVITEE_EMAIL,
    ]
