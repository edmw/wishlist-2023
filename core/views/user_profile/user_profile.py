"""All about viewing a user’s profile."""

import logging

from core.views._base import LoginRequiredMixin
from core.views.user import UserDetailView

logger = logging.getLogger(__name__)


class UserProfileView(LoginRequiredMixin, UserDetailView):
    """The view for a user profile."""

    http_method_names = ["get", "head", "options"]

    page_title = "Profile"
    template_name = "user_profile/user_profile.html"
