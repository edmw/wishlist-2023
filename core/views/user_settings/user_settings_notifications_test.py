"""All about updating a user’s settings test."""

import logging
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from core.services import NotificationService
from core.views._base import LoginRequiredMixin
from core.views.user import UserDetailView

logger = logging.getLogger(__name__)


class UserSettingsNotificationsTestView(LoginRequiredMixin, UserDetailView):
    """The view to edit a user settings test."""

    http_method_names = ["post", "head", "options"]

    page_title = "Test Notifications"
    template_name = "user_settings/user_settings_notifications_test.html"

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = self.try_user()

        self.send_result = NotificationService.send(
            user=user,
            subject=_("Notification"),
            template_name="user_settings/notifications/test.txt",
            html_template_name="user_settings/notifications/test.html",
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["send_result"] = getattr(self, "send_result", None)
        return context
