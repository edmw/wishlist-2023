"""All about viewing a user’s settings."""

import logging

from core.views._base import LoginRequiredMixin
from core.views.user import UserDetailView

logger = logging.getLogger(__name__)


class UserSettingsView(LoginRequiredMixin, UserDetailView):
    """The view for a user settings."""

    http_method_names = ["get", "head", "options"]

    page_title = "Settings"
    template_name = "user_settings/user_settings.html"
