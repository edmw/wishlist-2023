"""All about updating a user’s profile."""

import logging

from django.forms import ModelForm, Select, TextInput, ValidationError
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import User
from core.services import UserService
from core.views._base import LoginRequiredMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    SelectStylesMixin,
    TextStylesMixin,
)
from core.views.user import UserUpdateView

logger = logging.getLogger(__name__)


class UsernameWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    TextInput,
):
    label_text = gettext_noop("Nickname")
    placeholder_text = gettext_noop("Enter nickname")


class LanguageWidget(
    LabelBeforeMixin,
    AriaDescribedByMixin,
    SelectStylesMixin,
    Select,
):
    label_text = gettext_noop("Language")


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = [User.Fields.USERNAME, User.Fields.LANGUAGE]
        widgets = {
            User.Fields.USERNAME: UsernameWidget,
            User.Fields.LANGUAGE: LanguageWidget,
        }

    def clean_username(self) -> str:
        """Validates that the username is case-insensitive unique. The default
        validation allows usernames in different upper and lower case. A unique
        constraint in the model prevents usernames from being saved in different
        case. Without this validation, saving the form would fail with a generic
        unique constraint error.
        """
        username = self.cleaned_data.get("username")
        if username:
            # get user for the entered username case-insensitive
            user = UserService.find_user_for_username(username=username)
            if user and user != self.instance:
                # if a user was found and it is not the to be edited user
                # fail for a duplicate username
                raise ValidationError(_("This nickname is already in use by another user."))
        return username


class UserProfileUpdateView(LoginRequiredMixin, UserUpdateView):
    """The view to edit a user profile."""

    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Edit your Data")
    form_class = UserProfileForm
    template_name = "user_profile/user_profile_update.html"

    success_message = gettext_noop("Your updated data has been successfully saved.")
