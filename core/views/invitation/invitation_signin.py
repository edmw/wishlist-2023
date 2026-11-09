from typing import Any

from django.utils.translation import gettext_noop

from core import constants
from core.apps import CoreConfig
from core.models.types import InvitationState
from core.services import InvitationService
from core.views._base import TemplateView
from webapp.views import AddNeverCacheMixin


class InvitationSigninView(AddNeverCacheMixin, TemplateView):
    """The sign-in page for anonymous users who followed an invitation link.

    `InvitationAcceptView` parks the invitation code in the session and sends
    the invitee here; once they have logged in or signed up, a signal handler
    redirects them back to the invitation page, where they explicitly accept or
    decline (see ADR-1000). This page only explains that an invitation is
    waiting for them — it does not reveal any details about it (see REQ-2.21) —
    and offers the sign-in options.

    If no valid invitation is parked — for example because the user navigated
    here directly or the invitation can no longer be accepted — the generic
    sign-in content is shown instead, including any access restriction notice.
    """

    http_method_names = ["get", "head", "options"]

    template_name = "invitation/signin.html"
    page_title = gettext_noop("Sign in")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        code = self.request.session.get(constants.INVITATION_CODE_SESSION_KEY)
        invitation = InvitationService.get_invitation_by_code(code=code) if code else None
        context["signup_open"] = InvitationService.is_signup_open(code=code, access=CoreConfig.access)
        context["has_invitation"] = (
            invitation is not None and invitation.state in InvitationState.OPEN_STATES
        )
        return context
