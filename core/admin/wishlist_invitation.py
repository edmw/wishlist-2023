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
                    WishlistInvitation.Fields.VARIANT,
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    WishlistInvitation.Fields.CREATED_AT,
                    WishlistInvitation.Fields.STATE,
                    WishlistInvitation.Fields.SENT_AT,
                    WishlistInvitation.Fields.ACCEPTED_AT,
                    WishlistInvitation.Fields.DECLINED_AT,
                    WishlistInvitation.Fields.REVOKED_AT,
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
        WishlistInvitation.Fields.DECLINED_AT,
        WishlistInvitation.Fields.REVOKED_AT,
    )

    list_display = (
        WishlistInvitation.Fields.WISHLIST,
        WishlistInvitation.Fields.INVITER,
        WishlistInvitation.Fields.INVITEE_EMAIL,
        WishlistInvitation.Fields.VARIANT,
        WishlistInvitation.Fields.STATE,
        WishlistInvitation.Fields.CREATED_AT,
    )

    list_filter = (WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.VARIANT)

    search_fields = [
        WishlistInvitation.Fields.ID,
        WishlistInvitation.Fields.INVITEE_EMAIL,
    ]
