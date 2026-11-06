import logging
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core import constants
from core.services import (
    InvitationAlreadyAcceptedError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationService,
)
from core.views._base import TemplateView, UserMixin
from webapp.views import AddNeverCacheMixin

logger = logging.getLogger(__name__)


class InvitationAcceptView(UserMixin, AddNeverCacheMixin, TemplateView):
    """The public view for accepting an invitation to a wish list.

    An authenticated user accepts the invitation immediately and is redirected
    to the invited wish list. An anonymous user has the invitation code parked
    in their session and is sent to a dedicated sign-in page; once they have
    logged in or signed up, a signal handler accepts the parked invitation
    automatically (see ADR-1000).

    Invitations that are invalid, expired or already accepted cannot be
    accepted any more; instead of acting on them, this view renders a page
    explaining why.
    """

    http_method_names = ["get", "head", "options"]

    template_name = "invitation/accept.html"
    page_title = gettext_noop("Invitation")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        code = str(kwargs.get(constants.INVITATION_CODE_KEY) or "")
        invitation = InvitationService.get_invitation_by_code(code=code)

        if invitation is None:
            logger.info("Invitation accept requested for an unknown code.")
            return self._render_outcome(request, outcome="invalid", status=404)

        if invitation.expired:
            return self._render_outcome(request, outcome="expired")

        if invitation.accepted:
            # The invitation has been consumed already; accepting it again is
            # not possible. The invitee can still view the list through its
            # visibility, so point them there.
            messages.info(request, _("This invitation has already been accepted."))
            return redirect(invitation.wishlist.get_absolute_url())

        if user := self.user:
            try:
                accepted = InvitationService.accept_invitation(code=code, user=user)
            except InvitationNotFoundError:
                # The invitation was removed between the lookup and the accept.
                return self._render_outcome(request, outcome="invalid", status=404)
            except InvitationExpiredError:
                return self._render_outcome(request, outcome="expired")
            except InvitationAlreadyAcceptedError:
                messages.info(request, _("This invitation has already been accepted."))
                return redirect(invitation.wishlist.get_absolute_url())

            messages.success(request, _("The invitation has been accepted."))
            return redirect(accepted.wishlist.get_absolute_url())

        # The user is not authenticated yet; park the code in the session so
        # that it can be accepted automatically after login or sign-up. The
        # dedicated sign-in page explains this to the invitee and carries them
        # on from there.
        request.session[constants.INVITATION_CODE_SESSION_KEY] = str(invitation.code)
        next_url = urlencode({"next": invitation.wishlist.get_absolute_url()})
        return redirect(f"{reverse(constants.VIEW_INVITATION_SIGNIN)}?{next_url}")

    def _render_outcome(self, request: HttpRequest, *, outcome: str, status: int = 200) -> HttpResponse:
        """Renders the page explaining why an invitation could not be accepted.

        Arguments:
            request: The current request.
            outcome: One of "invalid", "expired" or "accepted"; selects the
                message to display in the template.
            status: HTTP status code for the rendered response.

        Returns:
            The rendered response.
        """
        context = self.get_context_data(outcome=outcome)
        response = self.render_to_response(context)
        response.status_code = status
        return response
