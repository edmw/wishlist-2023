"""User model representation in admin site."""
from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from core.models import User
from core.models.user_settings import UserSettings


class UserSettingsInline(admin.StackedInline):
    """UserSettings model representation inside User model representation."""

    model = UserSettings
    fk_name = UserSettings.Fields.USER
    can_delete = False
    view_on_site = False


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    """User model representation in admin site."""

    view_on_site = False

    inlines = [
        UserSettingsInline,
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    User.Fields.ID,
                    User.Fields.USERNAME,
                    User.Fields.FIRST_NAME,
                    User.Fields.LAST_NAME,
                    User.Fields.FULL_NAME,
                    User.Fields.EMAIL,
                    User.Fields.LANGUAGE,
                    User.Fields.LANGUAGE_SOFT,
                )
            },
        ),
        (
            "Modifiers",
            {"fields": (User.Fields.IS_STAFF,)},
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    User.Fields.CREATED_AT,
                    User.Fields.MODIFIED_AT,
                    User.Fields.IS_ACTIVE,
                    User.Fields.DEPROVISIONED,
                    User.Fields.DEPROVISIONED_AT,
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    User.Fields.USERNAME,
                    "password1",
                    "password2",
                    User.Fields.FIRST_NAME,
                    User.Fields.LAST_NAME,
                    User.Fields.EMAIL,
                    User.Fields.LANGUAGE,
                )
            },
        ),
    )

    readonly_fields = (
        User.Fields.ID,
        User.Fields.LANGUAGE_SOFT,
        User.Fields.CREATED_AT,
        User.Fields.MODIFIED_AT,
    )

    list_display = (
        User.Fields.USERNAME,
        User.Fields.EMAIL,
        User.Fields.IS_STAFF,
        User.Fields.IS_ACTIVE,
        User.Fields.DEPROVISIONED,
        User.Fields.CREATED_AT,
    )
