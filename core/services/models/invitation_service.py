"""Invitation services."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from allauth.account.models import EmailAddress
from django.conf import settings as django_settings
from django.utils.translation import gettext_noop

from core.access import CoreAccess
from core.models import User, Wishlist, WishlistInvitation
from core.models.types import (
    InvitationEmail,
    InvitationState,
    InvitationVariant,
    Visibility,
)
from core.services.framework.notification_service import NotificationService, TemplatedNotification
from core.services.models.favorite_service import FavoriteService
from core.services.models.wishlist_collaboration_service import WishlistCollaborationService

logger = logging.getLogger(__name__)

# The variant used when a caller does not specify one explicitly.
DEFAULT_INVITATION_VARIANT = InvitationVariant(InvitationVariant.NOTIFY)

# Notifications for the two invitation variants (see REQ-2.14). The subject is
# expected in the default language and translated at send time; the body is
# rendered in the owner's language.
INVITATION_EMAIL_NOTIFY = TemplatedNotification(
    subject=gettext_noop("Invitation to a wish list"),
    template_name="email/invitation_wishlist_notify.txt",
    html_template_name="email/invitation_wishlist_notify.html",
)

INVITATION_EMAIL_EDITOR = TemplatedNotification(
    subject=gettext_noop("Invitation to a wish list with editor offer"),
    template_name="email/invitation_wishlist_editor.txt",
    html_template_name="email/invitation_wishlist_editor.html",
)


class InvitationServiceError(Exception):
    pass


class InvitationAccessClosedError(InvitationServiceError):
    # Invitations are not allowed while the access mode is NOBODY (see REQ-2.4).
    pass


class InvitationLimitExceededError(InvitationServiceError):
    # The owner reached the daily limit of invitations (see REQ-2.8/REQ-2.9).
    pass


class InvitationPrivateWishlistError(InvitationServiceError):
    # Invitations cannot be created for, or accepted on, private wish lists
    # (see REQ-2.3, REQ-2.30/REQ-2.31).
    pass


class InvitationAlreadySentError(InvitationServiceError):
    pass


class InvitationNotSendableError(InvitationServiceError):
    # The plaintext token is no longer available, so no link can be built
    # (see REQ-2.17).
    pass


# All failures to accept or decline an invitation — unknown token, non-pending
# state (including derived EXPIRED), closed access mode and address mismatch —
# map to this single error, so that callers can respond identically without
# revealing details (see REQ-2.22).
class InvitationInvalidError(InvitationServiceError):
    pass


class InvitationService:
    """Invitation service: The Core’s invitation service provides functions for
    creating, sending and accepting invitations.

    Creating and sending an invitation is a two-step process (see ADR-1000):
    `create_invitation` initialises the invitation in state `CREATED`, and
    `send_invitation` hands it over to the mail transport and moves it to
    state `PENDING`. Because only a hash of the token is stored, sending must
    happen while the plaintext token is still available on the instance.

    Accepting an invitation adds the wish list to the acceptor's favorites; it
    does not grant any additional access (see ADR-1000). The editor offer of
    variant `EDITOR` is only taken up by a separate, active consent after the
    acceptance (see REQ-2.34/REQ-2.44).
    """

    @staticmethod
    def create_invitation(
        *,
        wishlist: Wishlist,
        inviter: User,
        invitee_email: str,
        variant: InvitationVariant = DEFAULT_INVITATION_VARIANT,
        access: CoreAccess,
    ) -> WishlistInvitation:
        """Creates a new invitation for the specified wish list addressed to
        the specified email address. The invitation is not sent yet; use
        `send_invitation` to deliver it.

        A random token is generated for the invitation; only its hash is
        stored, while the plaintext token stays available on the returned
        instance so that the link can be built when sending (see REQ-2.17).
        Any earlier open invitation for the same wish list and email address
        is revoked and replaced by the new one (see REQ-2.10).

        Arguments:
            wishlist: Wish list the invitation should apply to.
            inviter: User who issues the invitation.
            invitee_email: Email address of the person being invited. This may
                be an unregistered person.
            variant: Variant of the invitation; `NOTIFY` by default.
            access: The configured access mode of the application.

        Returns:
            The newly created, unsent invitation in state `CREATED`.

        Raises:
            InvitationAccessClosedError: If the access mode is NOBODY; no new
                accounts can be created at all in this mode (see REQ-2.4).
            InvitationPrivateWishlistError: If the wish list is private;
                invitations cannot be sent for private wish lists (see ADR-1000).
            InvitationLimitExceededError: If the owner reached the daily limit
                of invitations (see REQ-2.8/REQ-2.9).
        """
        if access == CoreAccess.NOBODY:
            raise InvitationAccessClosedError()

        if wishlist.visibility == Visibility.PRIVATE:
            raise InvitationPrivateWishlistError()

        InvitationService._ensure_daily_limit(inviter=inviter)

        # A new invitation replaces any earlier open one for the same wish list
        # and email address; the replaced ones become REVOKED (see REQ-2.10).
        # The match is case-insensitive on the normalized address, without alias
        # handling (see REQ-2.19).
        WishlistInvitation.objects.filter(
            wishlist=wishlist,
            invitee_email_field__iexact=invitee_email,
            state_field__in=InvitationState.OPEN_STATES,
        ).update(state_field=InvitationState.REVOKED, revoked_at=datetime.now(UTC))

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
    def _ensure_daily_limit(*, inviter: User) -> None:
        """Rejects a new invitation if the owner reached the daily limit.

        The limit counts every invitation created by the owner within the last
        24 hours, in any state — replacements and resends included (see
        REQ-2.8/REQ-2.9).

        Arguments:
            inviter: User who issues the invitation.

        Raises:
            InvitationLimitExceededError: If the daily limit is reached.
        """
        since = datetime.now(UTC) - timedelta(hours=24)
        recent_count = WishlistInvitation.objects.filter(inviter=inviter, created_at__gte=since).count()
        if recent_count >= django_settings.WISHLIST_INVITATION_DAILY_LIMIT:
            raise InvitationLimitExceededError()

    @staticmethod
    def send_invitation(*, invitation: WishlistInvitation) -> None:
        """Sends the specified invitation to its invitee.

        Hands an email containing the personal invitation link over to the mail
        transport and moves the invitation from state `CREATED` to `PENDING`.
        The delivery channel is chosen at this service layer; it is not part of
        the model hierarchy (see ADR-1000).

        The presentation (subject and templates) is chosen by the variant of
        the invitation, and the language is always that of the owner — English
        if the owner has no language available (see REQ-2.14/REQ-2.15).

        Arguments:
            invitation: Invitation to send. It must have been created before
                and must not have been sent yet; its plaintext token must
                still be available on the instance (see REQ-2.17).

        Raises:
            InvitationAlreadySentError: If the invitation was already sent or
                is in a final state.
            InvitationNotSendableError: If the plaintext token of the
                invitation is no longer available, so that no link can be
                built for delivery.
        """
        if invitation.state_field != InvitationState.CREATED:
            raise InvitationAlreadySentError()

        if not (token := invitation.token):
            raise InvitationNotSendableError()

        inviter = invitation.inviter
        # The owner's name is the concatenation of first and last name, but
        # only when both are present; otherwise the username is used, so that
        # the email never contains an empty or partial name (see REQ-2.14).
        if inviter.first_name and inviter.last_name:
            inviter_name = f"{inviter.first_name} {inviter.last_name}"
        else:
            inviter_name = inviter.username

        context: dict[str, Any] = {
            "inviter_name": inviter_name,
            "wishlist_name": str(invitation.wishlist.name),
            "invitation_url": invitation.get_absolute_accept_url(token=token),
            # The expiry duration is passed in seconds and humanized by the
            # template filter in the email's active language.
            "expires_after": WishlistInvitation.expires_after_seconds(),
        }

        notification = (
            INVITATION_EMAIL_EDITOR
            if invitation.variant == InvitationVariant.EDITOR
            else INVITATION_EMAIL_NOTIFY
        )

        NotificationService.send_email(
            address=str(invitation.invitee_email),
            notification=notification,
            language_code=inviter.get_language().get_code(),
            context=context,
        )

        invitation.state_field = InvitationState.PENDING
        invitation.sent_at = datetime.now(UTC)
        invitation.save(update_fields=[WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.SENT_AT])

    @staticmethod
    def accept_invitation(*, code: str, user: User, access: CoreAccess) -> WishlistInvitation:
        """Accepts the invitation with the specified token on behalf of the
        specified user.

        The invitation must be PENDING (not expired), the access mode must not
        be NOBODY, and one of the user's verified email addresses must match
        the invitation address case-insensitively. Accepting adds the wish list
        to the user's favorites; it does not grant any additional access,
        because invitations exist only for wish lists whose visibility already
        covers the invitee (see REQ-2.18/REQ-2.30/REQ-2.32/REQ-2.33).

        Arguments:
            code: The plaintext invitation token presented in the link. Only
                its hash is stored and compared (see REQ-2.17).
            user: User who accepts the invitation.
            access: The configured access mode of the application.

        Returns:
            The accepted invitation.

        Raises:
            InvitationInvalidError: If the token is unknown, the invitation is
                not PENDING (including derived EXPIRED), the access mode is
                NOBODY, or no verified email address of the user matches the
                invitation address. All these cases are intentionally mapped to
                a single error so that callers can respond identically without
                revealing details (see REQ-2.22).
            InvitationPrivateWishlistError: If the wish list is private at the
                moment of acceptance; no favorite or editor relation is created
                in this case (see REQ-2.30/REQ-2.31).
        """
        invitation = InvitationService.get_pending_invitation(code=code, user=user, access=access)

        if invitation.wishlist.visibility == Visibility.PRIVATE:
            raise InvitationPrivateWishlistError()

        FavoriteService.add_favorite(user=user, wishlist=invitation.wishlist)

        invitation.state_field = InvitationState.ACCEPTED
        invitation.accepted_at = datetime.now(UTC)
        invitation.save(
            update_fields=[WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.ACCEPTED_AT]
        )

        invitation.was_accepted()
        return invitation

    @staticmethod
    def decline_invitation(*, code: str, user: User, access: CoreAccess) -> WishlistInvitation:
        """Declines the invitation with the specified token on behalf of the
        specified user.

        The same conditions apply as for accepting (see `accept_invitation`),
        except that the visibility of the wish list is not checked. Declining
        moves the invitation to the final state `DECLINED`; it creates neither
        a favorite nor an editor relation (see REQ-2.36).

        Arguments:
            code: The plaintext invitation token presented in the link. Only
                its hash is stored and compared (see REQ-2.17).
            user: User who declines the invitation.
            access: The configured access mode of the application.

        Returns:
            The declined invitation.

        Raises:
            InvitationInvalidError: If the token is unknown, the invitation is
                not PENDING (including derived EXPIRED), the access mode is
                NOBODY, or no verified email address of the user matches the
                invitation address (see REQ-2.22/REQ-2.42).
        """
        invitation = InvitationService.get_pending_invitation(code=code, user=user, access=access)

        invitation.state_field = InvitationState.DECLINED
        invitation.declined_at = datetime.now(UTC)
        invitation.save(
            update_fields=[WishlistInvitation.Fields.STATE, WishlistInvitation.Fields.DECLINED_AT]
        )

        return invitation

    @staticmethod
    def get_pending_invitation(*, code: str, user: User, access: CoreAccess) -> WishlistInvitation:
        """Returns the PENDING invitation addressed to one of the user's
        verified email addresses.

        All failure cases — unknown token, non-pending state (including
        derived EXPIRED), closed access mode and address mismatch — raise the
        same error so that callers can respond identically without revealing
        details (see REQ-2.18/REQ-2.19/REQ-2.20/REQ-2.22/REQ-2.42).

        Arguments:
            code: The plaintext invitation token to look up and check.
            user: User on whose behalf the invitation is checked.
            access: The configured access mode of the application.

        Returns:
            The matching invitation in state `PENDING`.

        Raises:
            InvitationInvalidError: If any of the checks fails.
        """
        if (invitation := InvitationService.get_invitation_by_code(code=code)) is None:
            raise InvitationInvalidError()

        if invitation.state != InvitationState.PENDING:
            raise InvitationInvalidError()

        if access == CoreAccess.NOBODY:
            raise InvitationInvalidError()

        if not InvitationService._has_verified_address(user=user, email=str(invitation.invitee_email)):
            raise InvitationInvalidError()

        return invitation

    @staticmethod
    def get_accepted_invitation(*, code: str, user: User, access: CoreAccess) -> WishlistInvitation:
        """Returns the ACCEPTED invitation addressed to one of the user's
        verified email addresses.

        This is used for the editor consent step, which happens after the
        invitation has been accepted and therefore no longer passes the checks
        of `get_pending_invitation` (see REQ-2.34/REQ-2.44). All failure cases
        — unknown token, non-accepted state, closed access mode and address
        mismatch — raise the same error so that callers can respond identically
        without revealing details (see REQ-2.22/REQ-2.42).

        Arguments:
            code: The plaintext invitation token to look up and check.
            user: User on whose behalf the invitation is checked.
            access: The configured access mode of the application.

        Returns:
            The matching invitation in state `ACCEPTED`.

        Raises:
            InvitationInvalidError: If any of the checks fails.
        """
        if (invitation := InvitationService.get_invitation_by_code(code=code)) is None:
            raise InvitationInvalidError()

        if invitation.state != InvitationState.ACCEPTED:
            raise InvitationInvalidError()

        if access == CoreAccess.NOBODY:
            raise InvitationInvalidError()

        if not InvitationService._has_verified_address(user=user, email=str(invitation.invitee_email)):
            raise InvitationInvalidError()

        return invitation

    @staticmethod
    def _has_verified_address(*, user: User, email: str) -> bool:
        """Returns true if the user has a verified email address matching the
        given one.

        The comparison is case-insensitive on the normalized address; alias
        handling (dots and `+` in the local part) is deliberately not applied
        (see REQ-2.19/REQ-2.20).

        Arguments:
            user: User whose verified email addresses are checked.
            email: Email address to match against.

        Returns:
            True if a matching verified email address exists, False otherwise.
        """
        return EmailAddress.objects.filter(user=user, verified=True, email__iexact=email).exists()

    @staticmethod
    def consent_editor(*, invitation: WishlistInvitation, user: User) -> None:
        """Makes the recipient of an accepted EDITOR invitation an editor of
        its wish list.

        The editor offer is only taken up by a separate, active action after
        the invitation has been accepted; it must not be implied by opening
        the link (see REQ-2.34/REQ-2.44). The owner of a wish list can never
        become its editor — the collaboration service rejects this with
        `WishlistCollaborationOwnerAsEditorError` (see REQ-2.6/REQ-2.35), which
        is propagated to the caller.

        Arguments:
            invitation: Invitation whose editor offer is taken up. It must be
                of variant EDITOR and in state ACCEPTED.
            user: User who consents to become an editor.

        Raises:
            InvitationServiceError: If the invitation is not of variant EDITOR
                or has not been accepted yet.
        """
        if invitation.variant != InvitationVariant.EDITOR:
            raise InvitationServiceError()

        if invitation.state != InvitationState.ACCEPTED:
            raise InvitationServiceError()

        WishlistCollaborationService.add_editor(wishlist=invitation.wishlist, user=user)

    @staticmethod
    def revoke_pending_for_wishlist(*, wishlist: Wishlist) -> None:
        """Revokes all open invitations of the specified wish list.

        Every invitation in one of the open states (`CREATED`, `PENDING`) is
        moved to the final state `REVOKED`. Revocation is only performed by
        the system — for example when the wish list becomes private (see
        REQ-2.27/REQ-2.28).

        Arguments:
            wishlist: Wish list whose open invitations are revoked.
        """
        WishlistInvitation.objects.filter(
            wishlist=wishlist,
            state_field__in=InvitationState.OPEN_STATES,
        ).update(state_field=InvitationState.REVOKED, revoked_at=datetime.now(UTC))

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

        * In public mode, sign-up is open to everyone.
        * In existing mode, sign-up is only possible on the basis of a valid
          invitation and only if registration through invitations is enabled
          by configuration (see REQ-2.39/REQ-2.40).
        * In nobody mode, no new accounts can be created at all, not even on
          the basis of an invitation (see REQ-2.42).

        Arguments:
            code: The invitation token to check, or `None` if no invitation is
                available.
            access: The configured access mode of the application.

        Returns:
            True if sign-up may proceed, False otherwise.
        """
        if access == CoreAccess.PUBLIC:
            return True
        if access == CoreAccess.NOBODY:
            return False
        return django_settings.INVITATION_REGISTRATION_ENABLED and InvitationService._has_valid_invitation(
            code=code
        )

    @staticmethod
    def _has_valid_invitation(*, code: str | None) -> bool:
        """Returns true if the given invitation token refers to an invitation
        that is currently PENDING.

        Arguments:
            code: The plaintext invitation token to check, or `None` if no
                invitation is available.

        Returns:
            True if a valid invitation is available for this token.
        """
        if not code:
            return False
        invitation = InvitationService.get_invitation_by_code(code=code)
        return invitation is not None and invitation.state == InvitationState.PENDING
