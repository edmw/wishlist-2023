"""Invitation services."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import humanize
from django.conf import settings as django_settings
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from core.models import User, Wishlist, WishlistInvitation
from core.models.types import InvitationCode, InvitationEmail, Language, Visibility
from core.services.models.user_service import UserService
from webapp.services import EmailTransportService, LanguageService

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

        The email is rendered in the invitee's language if they have an
        account, and in the inviter's language otherwise.

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

        inviter = invitation.inviter
        # Fall back to the username if the user has no full name set, so that
        # the email never contains an empty or dangling name.
        inviter_name = str(inviter.full_name) or inviter.username

        context: dict[str, Any] = {
            "invitation": invitation,
            "inviter_name": inviter_name,
            "wishlist_name": str(invitation.wishlist.name),
            "invitation_url": invitation.get_absolute_accept_url(),
        }

        with LanguageService.activated(
            language_code=InvitationService._language_for_email(
                invitee_email=str(invitee_email), inviter=inviter
            ).get_code()
        ):
            # Render the expiry duration in the email's active language so that
            # it matches the rest of the message.
            context["expires_after"] = InvitationService.expires_after_duration()
            subject = _("Invitation to a wish list")
            message = render_to_string(
                template_name="email/invitation_wishlist.txt",
                context=context,
            )
            html_message = render_to_string(
                template_name="email/invitation_wishlist.html",
                context=context,
            )

        EmailTransportService.send_to_address(
            address=str(invitee_email),
            subject=subject,
            message=message,
            html_message=html_message,
        )

        invitation.sent = True
        invitation.sent_at = datetime.now(UTC)
        invitation.save(update_fields=[WishlistInvitation.Fields.SENT, WishlistInvitation.Fields.SENT_AT])

    @staticmethod
    def expires_after_duration() -> str:
        """Returns the configured invitation expiry duration as a humanized
        string in the active language (e.g. "10 days").

        The duration is read from the settings key referenced by the
        `WishlistInvitation` model, so that the displayed value always matches
        the actual expiration rule.

        Returns:
            Humanized representation of the expiry duration.
        """
        expires_after = getattr(django_settings, WishlistInvitation.EXPIRES_AFTER_SETTINGS_KEY)
        return humanize.naturaldelta(timedelta(seconds=expires_after))

    @staticmethod
    def _language_for_email(*, invitee_email: str, inviter: User) -> Language:
        """Determines the language for an invitation email.

        The email is rendered in the invitee's language if they have an
        account; otherwise it falls back to the inviter's language. An
        unregistered invitee has no known preference, and the inviter knows
        the recipient best.

        Arguments:
            invitee_email: Email address of the person being invited.
            inviter: User who issues the invitation.

        Returns:
            The language to render the email in.
        """
        if (invitee := UserService.find_user_for_email(email=invitee_email)) is not None:
            return invitee.get_language()
        return inviter.get_language()

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
        if (invitation := InvitationService.get_invitation_by_code(code=code)) is None:
            raise InvitationNotFoundError()

        if invitation.expired:
            raise InvitationExpiredError()

        if invitation.accepted:
            raise InvitationAlreadyAcceptedError()

        invitation.accepted = True
        invitation.accepted_at = datetime.now(UTC)
        invitation.save(
            update_fields=[WishlistInvitation.Fields.ACCEPTED, WishlistInvitation.Fields.ACCEPTED_AT]
        )

        invitation.was_accepted()
        return invitation

    @staticmethod
    def get_invitation_by_code(*, code: str) -> WishlistInvitation | None:
        """Returns the invitation with the specified code.

        Arguments:
            code: The invitation code to look up.

        Returns:
            The matching invitation, or `None` if no such invitation exists.
        """
        try:
            return WishlistInvitation.objects.get(code_field=code)
        except WishlistInvitation.DoesNotExist:
            return None

    @staticmethod
    def is_signup_open(*, code: str | None) -> bool:
        """Returns true if sign-up may proceed on the basis of the given
        invitation code.

        Sign-up stays closed during the beta period (see ADR-1000): a new
        account can be created only on the basis of an invitation that exists
        and has neither expired nor been accepted already.

        Arguments:
            code: The invitation code to check, or `None` if no invitation is
                available.

        Returns:
            True if sign-up may proceed with this code, False otherwise.
        """
        if not code:
            return False
        invitation = InvitationService.get_invitation_by_code(code=code)
        if invitation is None or invitation.expired or invitation.accepted:
            return False
        return True
