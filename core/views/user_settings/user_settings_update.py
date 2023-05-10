"""All about updating a user’s settings."""

import logging
from typing import cast

from django.db.models import QuerySet
from django.forms import CheckboxInput, ModelForm, TextInput
from django.utils.translation import gettext_noop

from core.models import User, UserSettings
from core.views._base import LoginRequiredMixin
from core.views._forms import (
    AriaDescribedByMixin,
    CheckboxStylesMixin,
    LabelAfterMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    TextStylesMixin,
)
from core.views.user import UserUpdateView
from core.views.user._base import IsUserView

logger = logging.getLogger(__name__)


class EmailEnabledWidget(
    LabelAfterMixin,
    CheckboxStylesMixin,
    CheckboxInput,
):
    label_text = gettext_noop("Enable Email")


class PushoverEnabledWidget(
    LabelBeforeMixin,
    CheckboxStylesMixin,
    CheckboxInput,
):
    label_text = gettext_noop("Enable Pushover")


class PushoverKeyWidget(
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    placeholder_text = gettext_noop("Enter your User key for Pushover Service")


class UserSettingsForm(ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            UserSettings.Fields.EMAIL_ENABLED,
            UserSettings.Fields.PUSHOVER_ENABLED,
            UserSettings.Fields.PUSHOVER_KEY,
        ]
        widgets = {
            UserSettings.Fields.EMAIL_ENABLED: EmailEnabledWidget,
            UserSettings.Fields.PUSHOVER_ENABLED: PushoverEnabledWidget,
            UserSettings.Fields.PUSHOVER_KEY: PushoverKeyWidget,
        }


class UserSettingsUpdateView(LoginRequiredMixin, UserUpdateView):
    """The view to edit a user settings."""

    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Edit your Settings")
    form_class = UserSettingsForm
    template_name = "user_settings/user_settings_update.html"

    success_message = gettext_noop("Your updated settings have been successfully saved.")

    def get_object(self: IsUserView, queryset: QuerySet[User] | None = None) -> UserSettings:
        user_object = cast(User, super().get_object(queryset))
        self.user = user_object
        return user_object.settings
