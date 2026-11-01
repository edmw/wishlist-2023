"""Invitation services."""

import logging
import secrets
from typing import Any, Mapping

from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from core.models import User, Wishlist, WishlistInvitation
from core.models.types import InvitationCode, InvitationEmail, Visibility
from core.services.adapter.email_service import EmailService
from webapp.services import LanguageService

logger = logging.getLogger(__name__)


class InvitationServiceError(Exception):
    pass


class InvitationPrivateWishlistError(InvitationServiceError):
    pass


class InvitationAlreadySentError(InvitationServiceError):
    pass


class InvitationNotSendableError(InvitationServiceError):
    pass


class InvitationNotFoundError(InvitationServiceError):
    pass


class InvitationExpiredError(InvitationServiceError):
    pass


class InvitationAlreadyAcceptedError(InvitationServiceError):
    pass


class InvitationService:
    """Invitation service: The Core’s invitation service provides functions for
    creating, sending and accepting invitations.

    Creating and sending an invitation is a two-step process (see ADR-1000):
    `create_invitation` initialises the invitation with `sent == False`, and
    `send_invitation` marks it as sent and delivers it to the invitee through
    the transport adapter chosen at this service layer.
    """

    @staticmethod
    def create_invitation(*, wishlist: Wishlist, inviter: User, invitee_email: str) -> WishlistInvitation:
        """Creates a new invitation for the specified wish list addressed to
        the specified email address. The invitation is not sent yet; use
        `send_invitation` to deliver it.

        Arguments:
            wishlist: Wish list the invitation should apply to.
            inviter: User who issues the invitation.
            invitee_email: Email address of the person being invited. This may
                be an unregistered person.

        Returns:
            The newly created, unsent invitation.

        Raises:
            InvitationPrivateWishlistError: If the wish list is private;
                invitations cannot be sent for private wish lists (see ADR-1000).
        """
        if wishlist.visibility == Visibility.PRIVATE:
            raise InvitationPrivateWishlistError()

        invitation = WishlistInvitation(
            inviter=inviter,
            invitee_email=InvitationEmail(invitee_email),
            code=InvitationCode(secrets.token_urlsafe(nbytes=16)),
            wishlist=wishlist,
        )
        invitation.save()
        return invitation

    @staticmethod
    def send_invitation(*, invitation: WishlistInvitation) -> None:
        """Sends the specified invitation to its invitee.

        Marks the invitation as sent and delivers an email containing the
        invitation link with code through the email transport adapter. The
        delivery channel is chosen at this service layer; it is not part of
        the model hierarchy (see ADR-1000).

        Arguments:
            invitation: Invitation to send. It must have been created before
                and must not have been sent yet.

        Raises:
            InvitationNotSendableError: If the invitation has no invitee email
                address set.
            InvitationAlreadySentError: If the invitation was already sent.
        """
        if invitation.sent:
            raise InvitationAlreadySentError()

        if not (invitee_email := invitation.invitee_email):
            raise InvitationNotSendableError()

        subject = _("Invitation to a wish list")
        context: Mapping[str, Any] = {
            "invitation": invitation,
            "inviter_name": str(invitation.inviter.full_name),
            "wishlist_name": str(invitation.wishlist.name),
            "invitation_url": InvitationService.build_invitation_url(code=invitation.code),
        }

        with LanguageService.activated(language_code=invitation.inviter.get_language().get_code()):
            message = render_to_string(
                template_name="email/invitation_wishlist.txt",
                context=context,
            )
            html_message = render_to_string(
                template_name="email/invitation_wishlist.html",
                context=context,
            )

        EmailService.send_to_address(
            address=str(invitee_email),
            subject=subject,
            message=message,
            html_message=html_message,
        )

        invitation.sent = True
        invitation.sent_at = timezone.now()
        invitation.save(update_fields=[WishlistInvitation.Fields.SENT, WishlistInvitation.Fields.SENT_AT])

    @staticmethod
    def accept_invitation(*, code: str, user: User) -> WishlistInvitation:
        """Accepts the invitation with the specified code on behalf of the
        specified user.

        The caller is responsible for ensuring that the user is authorised to
        accept the invitation (see ADR-1000). Accepting a wishlist invitation
        does not grant any additional access; it only changes the status of
        the invitation, because invitations exist only for wish lists whose
        visibility already covers the invitee.

        Arguments:
            code: The invitation code to accept.
            user: User who accepts the invitation.

        Returns:
            The accepted invitation.

        Raises:
            InvitationNotFoundError: If no invitation with the specified code
                exists.
            InvitationExpiredError: If the invitation has expired after being
                sent.
            InvitationAlreadyAcceptedError: If the invitation was already
                accepted.
        """
        try:
            invitation = WishlistInvitation.objects.get(code_field=code)
        except WishlistInvitation.DoesNotExist as exc:
            raise InvitationNotFoundError() from exc

        if invitation.expired:
            raise InvitationExpiredError()

        if invitation.accepted:
            raise InvitationAlreadyAcceptedError()

        invitation.accepted = True
        invitation.accepted_at = timezone.now()
        invitation.save(
            update_fields=[WishlistInvitation.Fields.ACCEPTED, WishlistInvitation.Fields.ACCEPTED_AT]
        )

        invitation.was_accepted()
        return invitation

    @staticmethod
    def build_invitation_url(*, code: InvitationCode) -> str:
        """Builds the absolute URL for accepting an invitation.

        The invitation link contains the invitation code so that the
        invitation is automatically marked as accepted after its first use
        (see ADR-1000).

        Arguments:
            code: The invitation code to include in the url.

        Returns:
            Absolute URL for accepting the invitation.
        """
        # NOTE: The path must match the route of the public accept view (see
        # PLAN.md, Phase 4). Once that view exists, switch this to reverse().
        from django.conf import settings as django_settings

        return f"{django_settings.WEBAPP_LOCATION}/invitations/{code}/"
