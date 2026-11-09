from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core import constants
from core.apps import CoreConfig
from core.models import User, WishlistInvitation
from core.models.types import InvitationState, InvitationVariant, Visibility
from core.services import (
    InvitationInvalidError,
    InvitationPrivateWishlistError,
    InvitationService,
    InvitationServiceError,
    WishlistCollaborationOwnerAsEditorError,
    WishlistCollaborationPrivateWishlistError,
)
from core.views._base import TemplateView, UserMixin
from webapp.views import AddNeverCacheMixin


class InvitationAcceptView(UserMixin, AddNeverCacheMixin, TemplateView):
    """The public view for acting on an invitation to a wish list.

    An authenticated user whose verified address matches the invitation sees
    an action page with explicit "accept" and "decline" buttons; the invitation
    is only acted upon by that active POST (see REQ-2.32). Accepting an
    invitation of variant EDITOR leads to a separate consent step for the editor
    role afterwards (see REQ-2.34/REQ-2.44).

    An anonymous user with a valid, pending invitation has the code parked in
    their session and is sent to a dedicated sign-in page; after login or
    sign-up they are redirected back here to act on the invitation (see ADR-1000).

    Every other case — unknown token, non-pending state (including derived
    EXPIRED), closed access mode, address mismatch and private wish lists —
    renders one identical page with a uniform status code, so that no details
    are revealed (see REQ-2.21/REQ-2.22).
    """

    http_method_names = ["get", "post", "head", "options"]

    template_name = "invitation/accept.html"
    page_title = gettext_noop("Invitation")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        code = str(kwargs.get(constants.INVITATION_CODE_KEY) or "")

        if user := self.user:
            try:
                invitation = InvitationService.get_pending_invitation(
                    code=code, user=user, access=CoreConfig.access
                )
            except InvitationInvalidError:
                # Unknown token, non-pending state (including derived EXPIRED),
                # closed access mode and address mismatch all map to the same
                # outcome; no details are revealed (see REQ-2.18/REQ-2.20/REQ-2.22).
                return self._render_invalid(request)

            if invitation.wishlist.visibility == Visibility.PRIVATE:
                # A list that became private cannot be accepted any more; the
                # uniform invalid response is rendered (see REQ-2.30/REQ-2.31).
                return self._render_invalid(request)

            context = self.get_context_data(invitation=invitation)
            return self.render_to_response(context)

        # The user is not authenticated yet; only a valid, pending invitation
        # may be parked in the session so that it can be acted on after login or
        # sign-up. Anything else gets the uniform invalid response (see
        # REQ-2.17/REQ-2.21/REQ-2.22).
        invitation = InvitationService.get_invitation_by_code(code=code)
        if invitation is None or invitation.state != InvitationState.PENDING:
            return self._render_invalid(request)

        request.session[constants.INVITATION_CODE_SESSION_KEY] = code
        return redirect(reverse(constants.VIEW_INVITATION_SIGNIN))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = self.try_user()
        code = str(kwargs.get(constants.INVITATION_CODE_KEY) or "")
        action = str(request.POST.get("action") or "")

        if action == "consent":
            return self._post_consent(request, user=user, code=code)

        if action == "accept":
            try:
                accepted = InvitationService.accept_invitation(
                    code=code, user=user, access=CoreConfig.access
                )
            except InvitationInvalidError, InvitationPrivateWishlistError:
                # Unknown token, non-pending state (including derived EXPIRED),
                # closed access mode, address mismatch and a list that is private
                # at acceptance time all map to the same outcome; no details are
                # revealed (see REQ-2.22/REQ-2.31).
                return self._render_invalid(request)

            if accepted.variant == InvitationVariant.EDITOR:
                # The editor offer is only taken up by a separate, active consent
                # after the acceptance (see REQ-2.34/REQ-2.44); the consent page
                # is rendered as the response to this POST.
                return self._render_consent(request, invitation=accepted)

            messages.success(request, _("The invitation has been accepted."))
            return redirect(accepted.wishlist.get_absolute_url())

        if action == "decline":
            try:
                InvitationService.decline_invitation(code=code, user=user, access=CoreConfig.access)
            except InvitationInvalidError:
                return self._render_invalid(request)

            messages.info(request, _("The invitation has been declined."))
            return redirect("/")

        # Any other action is not offered by the form; treat it like an invalid
        # presentation of the link (see REQ-2.22).
        return self._render_invalid(request)

    def _post_consent(self, request: HttpRequest, *, user: User, code: str) -> HttpResponse:
        """Handles the explicit consent to become an editor of the wish list.

        The invitation must have been accepted already and be addressed to one
        of the user's verified email addresses; otherwise the uniform invalid
        response is rendered (see REQ-2.34/REQ-2.44). If the user is the owner
        of the wish list, the consent cannot be granted and the consent page is
        re-rendered with an error message instead (see REQ-2.35).

        Arguments:
            request: The current request.
            user: Authenticated user who consents to become an editor.
            code: The plaintext invitation token presented in the link.

        Returns:
            The rendered response.
        """
        try:
            invitation = InvitationService.get_accepted_invitation(
                code=code, user=user, access=CoreConfig.access
            )
        except InvitationInvalidError:
            return self._render_invalid(request)

        try:
            InvitationService.consent_editor(invitation=invitation, user=user)
        except WishlistCollaborationOwnerAsEditorError:
            # The owner of a wish list can never become its editor (see REQ-2.35);
            # the consent page is re-rendered with an error message instead.
            return self._render_consent(request, invitation=invitation, error=True)
        except InvitationServiceError, WishlistCollaborationPrivateWishlistError:
            # The invitation carries no editor offer any more or the wish list
            # has become private; treat it like an invalid presentation of the
            # link (see REQ-2.31/REQ-2.34).
            return self._render_invalid(request)

        messages.success(request, _("You are now an editor of the wish list."))
        return redirect(invitation.wishlist.get_absolute_url())

    def _render_invalid(self, request: HttpRequest) -> HttpResponse:
        """Renders the page explaining that an invitation is not valid.

        All invalidity reasons share this single response with a uniform status
        code, so that no details are revealed (see REQ-2.22).

        Arguments:
            request: The current request.

        Returns:
            The rendered response with status 404.
        """
        context = self.get_context_data(outcome="invalid")
        response = self.render_to_response(context)
        response.status_code = 404
        return response

    def _render_consent(
        self, request: HttpRequest, *, invitation: WishlistInvitation, error: bool = False
    ) -> HttpResponse:
        """Renders the editor consent page for an accepted EDITOR invitation.

        Arguments:
            request: The current request.
            invitation: Accepted invitation whose editor offer is on display.
            error: Whether to show the error message that the consent could not
                be granted (see REQ-2.35).

        Returns:
            The rendered response.
        """
        context = self.get_context_data(invitation=invitation, consent_error=error)
        return TemplateResponse(request, "invitation/consent.html", context)
