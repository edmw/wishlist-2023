"""Invitation services."""

import logging
import secrets
from datetime import UTC, datetime
from typing import Any

from core.access import CoreAccess
from core.models import User, Wishlist, WishlistInvitation
from core.models.types import (
    InvitationEmail,
    InvitationState,
    InvitationVariant,
    Language,
    Visibility,
)
from core.services.framework.notification_service import NotificationService, TemplatedNotification
from core.services.models.user_service import UserService

logger = logging.getLogger(__name__)

# The variant used when a caller does not specify one explicitly.
DEFAULT_INVITATION_VARIANT = InvitationVariant(InvitationVariant.NOTIFY)


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
    `create_invitation` initialises the invitation in state `CREATED`, and
    `send_invitation` hands it over to the mail transport and moves it to
    state `PENDING`. Because only a hash of the token is stored, sending must
    happen while the plaintext token is still available on the instance.
    """

    @staticmethod
    def create_invitation(
        *,
        wishlist: Wishlist,
        inviter: User,
        invitee_email: str,
        variant: InvitationVariant = DEFAULT_INVITATION_VARIANT,
    ) -> WishlistInvitation:
        """Creates a new invitation for the specified wish list addressed to
        the specified email address. The invitation is not sent yet; use
        `send_invitation` to deliver it.

        A random token is generated for the invitation; only its hash is
        stored, while the plaintext token stays available on the returned
        instance so that the link can be built when sending (see REQ-2.17).

        Arguments:
            wishlist: Wish list the invitation should apply to.
            inviter: User who issues the invitation.
            invitee_email: Email address of the person being invited. This may
                be an unregistered person.
            variant: Variant of the invitation; `NOTIFY` by default.

        Returns:
            The newly created, unsent invitation in state `CREATED`.

        Raises:
            InvitationPrivateWishlistError: If the wish list is private;
                invitations cannot be sent for private wish lists (see ADR-1000).
        """
        if wishlist.visibility == Visibility.PRIVATE:
            raise InvitationPrivateWishlistError()

        token = secrets.token_urlsafe(nbytes=16)
        invitation = WishlistInvitation(
            inviter=inviter,
            invitee_email=InvitationEmail(invitee_email),
            code=WishlistInvitation.hash_token(token),
            variant=variant,
            wishlist=wishlist,
        )
        invitation.save()
        invitation._token = token
        return invitation

    @staticmethod
    def send_invitation(*, invitation: WishlistInvitation, email: TemplatedNotification) -> None:
        """Sends the specified invitation to its invitee.

        Hands an email containing the personal invitation link over to the
        mail transport and moves the invitation from state `CREATED` to
        `PENDING`. The delivery channel is chosen at this service layer; it is
        not part of the model hierarchy (see ADR-1000).

        The email's presentation (subject and templates) is provided by the
        caller, while the language is determined here: the email is rendered
        in the invitee's language if they have an account, and in the inviter's
        language otherwise.

        Arguments:
            invitation: Invitation to send. It must have been created before
                and must not have been sent yet; its plaintext token must
                still be available on the instance (see REQ-2.17).
            email: Subject and templates defining the email's presentation.

        Raises:
            InvitationExpiredError: If the invitation has expired before it
                was handed over to the mail transport.
            InvitationAlreadySentError: If the invitation was already sent or
                is in a final state.
            InvitationNotSendableError: If the plaintext token of the
                invitation is no longer available, so that no link can be
                built for delivery.
        """
        if (state := invitation.state) == InvitationState.EXPIRED:
            raise InvitationExpiredError()

        if state != InvitationState.CREATED:
            raise InvitationAlreadySentError()

        if not (token := invitation.token):
            raise InvitationNotSendableError()

        inviter = invitation.inviter
        # Fall back to the username if the user has no full name set, so that
        # the email never contains an empty or dangling name.
        inviter_name = str(inviter.full_name) or inviter.username

        context: dict[str, Any] = {
            "invitation": invitation,
            "inviter_name": inviter_name,
            "wishlist_name": str(invitation.wishlist.name),
            "variant": invitation.variant,
            "invitation_url": invitation.get_absolute_accept_url(token=token),
            # The expiry duration is passed in seconds and humanized by the
            # template filter in the email's active language.
            "expires_after": WishlistInvitation.expires_after_seconds(),
        }

        NotificationService.send_email(
            address=str(invitation.invitee_email),
            notification=email,
            language_code=InvitationService._language_for_email(
                invitee_email=str(invitation.invitee_email), inviter=inviter
            ).get_code(),
            context=context,
        )

        invitation.state_field = InvitationState.PENDING
        invitation.sent_at = datetime.now(UTC)
        invitation.save(update_fields=[WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.SENT_AT])

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
        """Accepts the invitation with the specified token on behalf of the
        specified user.

        The caller is responsible for ensuring that the user is authorised to
        accept the invitation (see ADR-1000). Accepting a wishlist invitation
        does not grant any additional access; it only changes the state of
        the invitation, because invitations exist only for wish lists whose
        visibility already covers the invitee.

        Arguments:
            code: The plaintext invitation token presented in the link. Only
                its hash is stored and compared (see REQ-2.17).
            user: User who accepts the invitation.

        Returns:
            The accepted invitation.

        Raises:
            InvitationNotFoundError: If no invitation with the specified token
                exists.
            InvitationExpiredError: If the invitation has expired.
            InvitationAlreadyAcceptedError: If the invitation is in a final
                state and cannot be accepted any more.
        """
        if (invitation := InvitationService.get_invitation_by_code(code=code)) is None:
            raise InvitationNotFoundError()

        if (state := invitation.state) == InvitationState.EXPIRED:
            raise InvitationExpiredError()

        if state != InvitationState.PENDING:
            raise InvitationAlreadyAcceptedError()

        invitation.state_field = InvitationState.ACCEPTED
        invitation.accepted_at = datetime.now(UTC)
        invitation.save(
            update_fields=[WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.ACCEPTED_AT]
        )

        invitation.was_accepted()
        return invitation

    @staticmethod
    def get_invitation_by_code(*, code: str) -> WishlistInvitation | None:
        """Returns the invitation with the specified token.

        The plaintext token is hashed before it is looked up; only the hash
        is stored (see REQ-2.17).

        Arguments:
            code: The plaintext invitation token to look up.

        Returns:
            The matching invitation, or `None` if no such invitation exists.
        """
        try:
            return WishlistInvitation.objects.get(code_field=WishlistInvitation.hash_token(code))
        except WishlistInvitation.DoesNotExist:
            return None

    @staticmethod
    def is_signup_open(*, code: str | None, access: CoreAccess) -> bool:
        """Returns true if sign-up may proceed.

        The decision follows the configured access mode (see ADR-1000):

        * Without a valid invitation, sign-up is open only in public mode.
        * With a valid invitation, sign-up is open unless nobody has been
          granted access at all.

        Arguments:
            code: The invitation token to check, or `None` if no invitation is
                available.
            access: The configured access mode of the application.

        Returns:
            True if sign-up may proceed, False otherwise.
        """
        if InvitationService._has_valid_invitation(code=code):
            return access != CoreAccess.NOBODY
        return access == CoreAccess.PUBLIC

    @staticmethod
    def _has_valid_invitation(*, code: str | None) -> bool:
        """Returns true if the given invitation token refers to an invitation
        that is still in one of the open states (`CREATED`, `PENDING`) and has
        not expired.

        Arguments:
            code: The plaintext invitation token to check, or `None` if no
                invitation is available.

        Returns:
            True if a valid invitation is available for this token.
        """
        if not code:
            return False
        invitation = InvitationService.get_invitation_by_code(code=code)
        return invitation is not None and invitation.state in InvitationState.OPEN_STATES
