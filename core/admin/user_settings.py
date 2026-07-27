"""UserSettings model representation in admin site."""

from django.contrib import admin

from core.models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """UserSettings model representation in admin site."""

    view_on_site = False  # type: ignore[assignment]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    UserSettings.Fields.ID,
                    UserSettings.Fields.USER,
                    UserSettings.Fields.EMAIL_ENABLED,
                    UserSettings.Fields.PUSHOVER_ENABLED,
                    UserSettings.Fields.PUSHOVER_KEY,
                )
            },
        ),
    )

    readonly_fields = (UserSettings.Fields.ID, UserSettings.Fields.USER)

    list_display = (
        UserSettings.Fields.USER,
        UserSettings.Fields.EMAIL_ENABLED,
        UserSettings.Fields.PUSHOVER_ENABLED,
    )

    list_filter = (
        (UserSettings.Fields.EMAIL_ENABLED, admin.BooleanFieldListFilter),
        (UserSettings.Fields.PUSHOVER_ENABLED, admin.BooleanFieldListFilter),
    )

    search_fields = [
        UserSettings.Fields.USER,
    ]
