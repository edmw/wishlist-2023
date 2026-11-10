"""Tests for the invitation service along the lines of req-0002."""

from typing import Any, Generator

import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from freezegun import freeze_time

from core.access import CoreAccess
from core.models import Favorite, User, Wishlist, WishlistInvitation
from core.models.types import InvitationState, InvitationVariant, Visibility
from core.services import (
    InvitationAccessClosedError,
    InvitationAlreadySentError,
    InvitationInvalidError,
    InvitationLimitExceededError,
    InvitationNotSendableError,
    InvitationPrivateWishlistError,
    InvitationService,
    InvitationServiceError,
    WishlistCollaborationOwnerAsEditorError,
    WishlistCollaborationService,
)
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"

# The baseline access mode for service-level tests; NOBODY and PUBLIC are
# exercised explicitly where the behavior differs.
ACCESS = CoreAccess.EXISTING


@pytest.fixture(autouse=True)
def _locmem_email(settings: Any) -> Generator[None, None, None]:
    """Ensures emails are captured in memory instead of being sent."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield
    mail.outbox = []


def _verified_email(user: User, email: str) -> EmailAddress:
    """Creates a verified allauth email address for the given user."""
    return EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)


def _users_list(owner: User) -> Wishlist:
    """Creates a wish list with visibility USERS owned by the given user."""
    return Wishlist.objects.create(
        owner=owner,
        name_field="Users list",
        description_field="",
        visibility_field=Visibility.USERS,
        item_ordering_field="+name",
    )


def _private_list(owner: User) -> Wishlist:
    """Creates a wish list with visibility PRIVATE owned by the given user."""
    return Wishlist.objects.create(
        owner=owner,
        name_field="Private list",
        description_field="",
        visibility_field=Visibility.PRIVATE,
        item_ordering_field="+name",
    )


def _sent_invitation(
    core: CoreFixture,
    *,
    wishlist: Wishlist | None = None,
    invitee_email: str = INVITEE_EMAIL,
    variant: InvitationVariant | None = None,
) -> WishlistInvitation:
    """Creates and sends an invitation; returns it in state PENDING."""
    kwargs: dict[str, Any] = {}
    if variant is not None:
        kwargs["variant"] = variant
    invitation = InvitationService.create_invitation(
        wishlist=wishlist or core.list_alice,
        inviter=core.user_alice,
        invitee_email=invitee_email,
        access=ACCESS,
        **kwargs,
    )
    InvitationService.send_invitation(invitation=invitation)
    return invitation


@pytest.mark.django_db
class TestCreateInvitation:
    """Creating invitations (see req-0002, acceptance criteria "Creating")."""

    def test_creates_pending_invitation_and_sends_mail(self, core: CoreFixture) -> None:
        """A NOTIFY invitation for a USERS list ends up PENDING with a mail handed over."""
        wishlist = _users_list(core.user_alice)

        invitation = InvitationService.create_invitation(
            wishlist=wishlist,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        assert invitation.state == InvitationState.CREATED

        InvitationService.send_invitation(invitation=invitation)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [INVITEE_EMAIL]

    def test_rejects_private_wishlist(self, core: CoreFixture) -> None:
        """No invitation can be created for a private wish list."""
        wishlist = _private_list(core.user_alice)

        with pytest.raises(InvitationPrivateWishlistError):
            InvitationService.create_invitation(
                wishlist=wishlist,
                inviter=core.user_alice,
                invitee_email=INVITEE_EMAIL,
                access=ACCESS,
            )

        assert WishlistInvitation.objects.filter(wishlist=wishlist).count() == 0

    def test_rejects_closed_access_mode(self, core: CoreFixture) -> None:
        """In access mode NOBODY no invitation can be created (see REQ-2.4)."""
        with pytest.raises(InvitationAccessClosedError):
            InvitationService.create_invitation(
                wishlist=core.list_alice,
                inviter=core.user_alice,
                invitee_email=INVITEE_EMAIL,
                access=CoreAccess.NOBODY,
            )

        assert WishlistInvitation.objects.count() == 0

    def test_allows_own_address_with_notify_variant(self, core: CoreFixture) -> None:
        """The owner may invite his own address with variant NOTIFY (see REQ-2.12)."""
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=str(core.user_alice.email),
            access=ACCESS,
        )

        assert invitation.pk is not None
        assert str(invitation.invitee_email) == str(core.user_alice.email)

    def test_rejects_when_daily_limit_reached(self, core: CoreFixture, settings: Any) -> None:
        """Once the owner reached the daily limit, further invitations are rejected."""
        settings.WISHLIST_INVITATION_DAILY_LIMIT = 3
        for index in range(3):
            _sent_invitation(core, invitee_email=f"invitee{index}@example.com")

        with pytest.raises(InvitationLimitExceededError):
            InvitationService.create_invitation(
                wishlist=core.list_alice,
                inviter=core.user_alice,
                invitee_email="another@example.com",
                access=ACCESS,
            )

        assert len(mail.outbox) == 3

    def test_rejects_sixth_invitation_with_limit_of_five(self, core: CoreFixture, settings: Any) -> None:
        """With a limit of five, the sixth invitation within a day is rejected."""
        settings.WISHLIST_INVITATION_DAILY_LIMIT = 5
        for index in range(5):
            _sent_invitation(core, invitee_email=f"invitee{index}@example.com")

        with pytest.raises(InvitationLimitExceededError):
            InvitationService.create_invitation(
                wishlist=core.list_alice,
                inviter=core.user_alice,
                invitee_email="sixth@example.com",
                access=ACCESS,
            )

    @freeze_time("2026-01-02 12:00:00")
    def test_daily_limit_uses_rolling_window(self, core: CoreFixture, settings: Any) -> None:
        """Invitations created more than 24 hours ago do not count towards the limit."""
        settings.WISHLIST_INVITATION_DAILY_LIMIT = 1

        with freeze_time("2026-01-01 11:59:00"):
            _sent_invitation(core)

        # More than 24 hours have passed, so the limit is free again.
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email="second@example.com",
            access=ACCESS,
        )

        assert invitation.pk is not None

    def test_replacements_count_towards_daily_limit(self, core: CoreFixture, settings: Any) -> None:
        """Replacements and resends are included in the daily limit (see REQ-2.9)."""
        settings.WISHLIST_INVITATION_DAILY_LIMIT = 2
        _sent_invitation(core)
        # Re-inviting the same address replaces the old invitation but still counts.
        _sent_invitation(core)

        with pytest.raises(InvitationLimitExceededError):
            InvitationService.create_invitation(
                wishlist=core.list_alice,
                inviter=core.user_alice,
                invitee_email="third@example.com",
                access=ACCESS,
            )


@pytest.mark.django_db
class TestReplaceInvitation:
    """Replacing and resending (see req-0002, acceptance criteria "Replacing and resending")."""

    def test_replaces_open_invitation(self, core: CoreFixture) -> None:
        """A new invitation for the same list and address revokes the open one."""
        old = _sent_invitation(core)

        new = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        InvitationService.send_invitation(invitation=new)

        old.refresh_from_db()
        new.refresh_from_db()
        assert old.state == InvitationState.REVOKED
        assert old.revoked_at is not None
        assert new.state == InvitationState.PENDING

    def test_old_link_becomes_invalid_after_replacement(self, core: CoreFixture) -> None:
        """The token of a replaced invitation can no longer be used."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        old = _sent_invitation(core)
        InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(code=str(old.token), user=core.user_bob, access=ACCESS)

    def test_replacement_matches_address_case_insensitively(self, core: CoreFixture) -> None:
        """The replacement match is case-insensitive on the address (see REQ-2.19)."""
        old = _sent_invitation(core, invitee_email="Invitee@Example.com")

        new = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email="invitee@example.com",
            access=ACCESS,
        )

        old.refresh_from_db()
        assert old.state == InvitationState.REVOKED
        assert new.pk is not None

    def test_reinvite_after_accepted(self, core: CoreFixture) -> None:
        """After acceptance a new invitation can be created; the old one stays ACCEPTED."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        old = _sent_invitation(core)
        InvitationService.accept_invitation(code=str(old.token), user=core.user_bob, access=ACCESS)

        new = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )

        old.refresh_from_db()
        assert old.state == InvitationState.ACCEPTED
        assert new.pk is not None
        assert new.pk != old.pk

    def test_reinvite_after_declined(self, core: CoreFixture) -> None:
        """After a decline a new invitation can be created; the old one stays DECLINED."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        old = _sent_invitation(core)
        InvitationService.decline_invitation(code=str(old.token), user=core.user_bob, access=ACCESS)

        new = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )

        old.refresh_from_db()
        assert old.state == InvitationState.DECLINED
        assert new.pk is not None


@pytest.mark.django_db
class TestSendInvitation:
    """Sending invitations and the mail content (see req-0002, acceptance criteria "Mail")."""

    def test_mail_contains_title_owner_and_link(self, core: CoreFixture) -> None:
        """The NOTIFY mail contains the list title, the owner name and the link."""
        invitation = _sent_invitation(core)

        message = mail.outbox[0]
        assert message.subject == "Invitation to a wish list"
        assert f"'{core.list_alice.name}'" in message.body
        assert "Alice Rivest has invited you" in message.body
        assert str(invitation.token) in message.body

    def test_editor_variant_mail_differs(self, core: CoreFixture) -> None:
        """The EDITOR mail has its own subject and offers the editor role."""
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))

        message = mail.outbox[0]
        assert message.subject == "Invitation to a wish list with editor offer"
        assert "You may also become an editor of this wish list." in message.body
        assert str(invitation.token) in message.body

    def test_uses_username_if_owner_has_no_full_name(self, core: CoreFixture) -> None:
        """The username is used if the owner has neither first nor last name."""
        inviter = User.objects.create(username="noname", email="noname@example.com")

        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=inviter,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        InvitationService.send_invitation(invitation=invitation)

        message = mail.outbox[0]
        assert "noname has invited you" in message.body
        assert "The invitation was sent by noname." in message.body

    def test_uses_username_if_owner_has_only_partial_name(self, core: CoreFixture) -> None:
        """A partial name (first or last only) falls back to the username as well."""
        inviter = User.objects.create(username="partial", email="partial@example.com", first_name="Only")

        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=inviter,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        InvitationService.send_invitation(invitation=invitation)

        message = mail.outbox[0]
        assert "partial has invited you" in message.body
        assert "Only has invited you" not in message.body

    def test_mail_is_in_owners_language(self, core: CoreFixture) -> None:
        """The mail is rendered in the owner's language (see REQ-2.15)."""
        inviter = User.objects.create(username="german", email="german@example.com", language_field="de")

        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=inviter,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        InvitationService.send_invitation(invitation=invitation)

        message = mail.outbox[0]
        assert message.subject == "Einladung zu einem Wunschzettel"
        assert f"hat dich zum Wunschzettel '{core.list_alice.name}' eingeladen" in message.body
        assert "Die Einladung wurde von german gesendet." in message.body
        assert "Die Einladung ist gültig für 10 Tage." in message.body

    def test_mail_falls_back_to_english_without_language(self, core: CoreFixture) -> None:
        """Without any available language of the owner, English is used (see REQ-2.15)."""
        # The fixture user has no explicit and no soft language set.
        assert str(core.user_alice.language) == ""

        _sent_invitation(core)

        message = mail.outbox[0]
        assert message.subject == "Invitation to a wish list"
        assert "has invited you" in message.body

    def test_mail_ignores_invitee_language(self, core: CoreFixture) -> None:
        """Even if the invitee has an account with another language, the owner's applies."""
        User.objects.create(username="invitee", email=INVITEE_EMAIL, language_field="de")

        _sent_invitation(core)

        message = mail.outbox[0]
        assert message.subject == "Invitation to a wish list"
        assert "has invited you" in message.body

    def test_marks_pending_and_drops_token(self, core: CoreFixture) -> None:
        """After the handover to the mail transport the invitation is PENDING."""
        invitation = _sent_invitation(core)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING
        assert invitation.sent_at is not None
        # The plaintext token is no longer available once reloaded from the database.
        assert invitation.token is None

    def test_raises_if_already_sent(self, core: CoreFixture) -> None:
        """Sending an invitation that was already sent fails."""
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationAlreadySentError):
            InvitationService.send_invitation(invitation=invitation)

    def test_raises_if_token_not_available(self, core: CoreFixture) -> None:
        """An invitation reloaded from the database carries no plaintext token."""
        invitation = _sent_invitation(core)
        invitation.refresh_from_db()
        # Force the stored state back to CREATED so that only the missing
        # token is what prevents sending.
        invitation.state_field = InvitationState.CREATED

        with pytest.raises(InvitationNotSendableError):
            InvitationService.send_invitation(invitation=invitation)


@pytest.mark.django_db
class TestTokenAndLink:
    """Tokens and links (see req-0002, acceptance criteria "Token and link")."""

    def test_only_hash_of_token_is_stored(self, core: CoreFixture) -> None:
        """Only the hash of the token is persisted; never the plaintext."""
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )

        token = str(invitation.token)
        assert len(token) > 0
        invitation.refresh_from_db()
        assert str(invitation.code) == WishlistInvitation.hash_token(token)
        assert str(invitation.code) != token

    def test_used_link_is_rejected_like_unknown(self, core: CoreFixture) -> None:
        """A used link fails with the same error as an unknown one (see REQ-2.18/REQ-2.22)."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        token = str(invitation.token)
        InvitationService.accept_invitation(code=token, user=core.user_bob, access=ACCESS)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(code=token, user=core.user_bob, access=ACCESS)
        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(code="does-not-exist", user=core.user_bob, access=ACCESS)

    def test_rejects_user_with_different_address(self, core: CoreFixture) -> None:
        """A signed-in user whose verified address differs cannot accept (see REQ-2.18)."""
        _verified_email(core.user_bob, "other@example.com")
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )

    def test_matches_address_case_insensitively(self, core: CoreFixture) -> None:
        """An invitation to Max@Example.com matches max@example.com (see REQ-2.19)."""
        _verified_email(core.user_bob, "max@example.com")
        invitation = _sent_invitation(core, invitee_email="Max@Example.com")

        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        assert accepted.pk == invitation.pk

    def test_does_not_normalize_dot_aliases(self, core: CoreFixture) -> None:
        """Dots in the local part are not normalized (see REQ-2.19)."""
        _verified_email(core.user_bob, "m.ax@gmail.com")
        invitation = _sent_invitation(core, invitee_email="max@gmail.com")

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )

    def test_rejects_unverified_address(self, core: CoreFixture) -> None:
        """A matching address that is not verified cannot accept (see REQ-2.20)."""
        EmailAddress.objects.create(user=core.user_bob, email=INVITEE_EMAIL, verified=False, primary=True)
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )


@pytest.mark.django_db
class TestLifecycle:
    """The lifecycle of invitations (see req-0002, acceptance criteria "Lifecycle")."""

    def test_starts_created_and_becomes_pending(self, core: CoreFixture) -> None:
        """A new invitation is CREATED and becomes PENDING after the handover."""
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
            access=ACCESS,
        )
        assert invitation.state == InvitationState.CREATED

        InvitationService.send_invitation(invitation=invitation)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    @freeze_time("2026-01-01 12:00:00")
    def test_expires_ten_days_after_creation(self, core: CoreFixture) -> None:
        """A PENDING invitation is EXPIRED ten days after creation and unusable."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        # Just before the expiry it is still PENDING.
        with freeze_time("2026-01-11 11:59:59"):
            assert WishlistInvitation.objects.get(pk=invitation.pk).state == InvitationState.PENDING

        # At exactly ten days after creation it is EXPIRED and cannot be accepted.
        with freeze_time("2026-01-11 12:00:00"):
            assert WishlistInvitation.objects.get(pk=invitation.pk).state == InvitationState.EXPIRED
            with pytest.raises(InvitationInvalidError):
                InvitationService.accept_invitation(
                    code=str(invitation.token), user=core.user_bob, access=ACCESS
                )

        invitation.refresh_from_db()
        # The stored state never changes because of time; only the derived one does.
        assert invitation.state_field == InvitationState.PENDING

    def test_final_states_do_not_change(self, core: CoreFixture) -> None:
        """Actions on invitations in final states leave the state unchanged."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        accepted = _sent_invitation(core)
        InvitationService.accept_invitation(code=str(accepted.token), user=core.user_bob, access=ACCESS)

        declined = _sent_invitation(core, invitee_email="decline@example.com")
        _verified_email(core.user_carol, "decline@example.com")
        InvitationService.decline_invitation(code=str(declined.token), user=core.user_carol, access=ACCESS)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(code=str(accepted.token), user=core.user_bob, access=ACCESS)
        with pytest.raises(InvitationAlreadySentError):
            InvitationService.send_invitation(invitation=accepted)
        with pytest.raises(InvitationInvalidError):
            InvitationService.decline_invitation(
                code=str(declined.token), user=core.user_carol, access=ACCESS
            )

        accepted.refresh_from_db()
        declined.refresh_from_db()
        assert accepted.state == InvitationState.ACCEPTED
        assert declined.state == InvitationState.DECLINED


@pytest.mark.django_db
class TestVisibilityChanges:
    """Revocation and visibility at acceptance (see req-0002, "Visibility changes")."""

    def test_revoke_pending_for_wishlist(self, core: CoreFixture) -> None:
        """All open invitations of a list are revoked; final states stay untouched."""
        pending = _sent_invitation(core)
        created = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email="second@example.com",
            access=ACCESS,
        )
        _verified_email(core.user_bob, "third@example.com")
        accepted = _sent_invitation(core, invitee_email="third@example.com")
        InvitationService.accept_invitation(code=str(accepted.token), user=core.user_bob, access=ACCESS)

        InvitationService.revoke_pending_for_wishlist(wishlist=core.list_alice)

        pending.refresh_from_db()
        created.refresh_from_db()
        accepted.refresh_from_db()
        assert pending.state == InvitationState.REVOKED
        assert pending.revoked_at is not None
        assert created.state == InvitationState.REVOKED
        assert accepted.state == InvitationState.ACCEPTED

    def test_accept_fails_when_list_becomes_private(self, core: CoreFixture) -> None:
        """A list that became private has its open invitations revoked; accepting fails."""
        wishlist = _users_list(core.user_alice)
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, wishlist=wishlist)

        wishlist.visibility = Visibility(Visibility.PRIVATE)
        wishlist.save(update_fields=[Wishlist.Fields.VISIBILITY])

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.REVOKED
        assert Favorite.objects.filter(user=core.user_bob, wishlist=wishlist).count() == 0
        assert not WishlistCollaborationService.is_editor(wishlist=wishlist, user=core.user_bob)

    def test_accept_fails_for_private_list_with_editor_variant(self, core: CoreFixture) -> None:
        """An EDITOR invitation for a now-private list cannot be accepted or consented."""
        wishlist = _users_list(core.user_alice)
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(
            core, wishlist=wishlist, variant=InvitationVariant(InvitationVariant.EDITOR)
        )

        wishlist.visibility = Visibility(Visibility.PRIVATE)
        wishlist.save(update_fields=[Wishlist.Fields.VISIBILITY])

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )

    def test_accept_fails_for_pending_invitation_on_private_list(self, core: CoreFixture) -> None:
        """A PENDING invitation on a private list is rejected at acceptance time.

        The visibility check in `accept_invitation` guards against invitations that
        are still open although the list is private (see REQ-2.30/REQ-2.31); the
        queryset update bypasses the model hook that normally revokes them.
        """
        wishlist = _users_list(core.user_alice)
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, wishlist=wishlist)

        Wishlist.objects.filter(pk=wishlist.pk).update(visibility_field=Visibility.PRIVATE)
        wishlist.refresh_from_db()

        with pytest.raises(InvitationPrivateWishlistError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=ACCESS
            )

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    def test_visibility_switch_keeps_pending(self, core: CoreFixture) -> None:
        """Switching between PUBLIC and USERS leaves PENDING invitations valid."""
        invitation = _sent_invitation(core)

        core.list_alice.visibility = Visibility(Visibility.USERS)
        core.list_alice.save(update_fields=[Wishlist.Fields.VISIBILITY])
        assert WishlistInvitation.objects.get(pk=invitation.pk).state == InvitationState.PENDING

        core.list_alice.visibility = Visibility(Visibility.PUBLIC)
        core.list_alice.save(update_fields=[Wishlist.Fields.VISIBILITY])
        _verified_email(core.user_bob, INVITEE_EMAIL)
        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        assert accepted.state == InvitationState.ACCEPTED


@pytest.mark.django_db
class TestAcceptingAndDeclining:
    """Accepting and declining (see req-0002, acceptance criteria "Accepting and declining")."""

    def test_accept_adds_favorite(self, core: CoreFixture) -> None:
        """Accepting adds the wish list to the recipient's favorites."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        assert accepted.state == InvitationState.ACCEPTED
        assert accepted.accepted_at is not None
        favorite = Favorite.objects.get(user=core.user_bob, wishlist=core.list_alice)
        # Accepting a notification enables item-create notifications (see REQ-2.33).
        assert favorite.notify_on_item_create is True

    def test_accept_keeps_existing_favorite(self, core: CoreFixture) -> None:
        """If the list is already a favorite, accepting does not create a duplicate."""
        Favorite.objects.create(user=core.user_bob, wishlist=core.list_alice, notify_on_item_create=False)
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        assert Favorite.objects.filter(user=core.user_bob, wishlist=core.list_alice).count() == 1

    def test_notify_variant_does_not_make_editor(self, core: CoreFixture) -> None:
        """Accepting a NOTIFY invitation does not create an editor relation."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_bob)

    def test_accepting_editor_variant_does_not_consent(self, core: CoreFixture) -> None:
        """Accepting an EDITOR invitation alone does not make the recipient an editor."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))

        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_bob)
        assert Favorite.objects.filter(user=core.user_bob, wishlist=core.list_alice).count() == 1

    def test_consent_makes_editor(self, core: CoreFixture) -> None:
        """Explicit consent after acceptance makes the recipient an editor."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))
        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        InvitationService.consent_editor(invitation=accepted, user=core.user_bob)

        assert WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_bob)
        assert Favorite.objects.filter(user=core.user_bob, wishlist=core.list_alice).count() == 1

    def test_consent_rejected_for_notify_variant(self, core: CoreFixture) -> None:
        """Consent is only possible for invitations of variant EDITOR."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        with pytest.raises(InvitationServiceError):
            InvitationService.consent_editor(invitation=accepted, user=core.user_bob)

    def test_consent_rejected_before_acceptance(self, core: CoreFixture) -> None:
        """Consent requires the invitation to be accepted already."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))

        with pytest.raises(InvitationServiceError):
            InvitationService.consent_editor(invitation=invitation, user=core.user_bob)

    def test_owner_cannot_consent_to_own_editor_offer(self, core: CoreFixture) -> None:
        """The owner accepting his own EDITOR invitation cannot become editor (see REQ-2.35)."""
        _verified_email(core.user_alice, str(core.user_alice.email))
        invitation = _sent_invitation(
            core,
            invitee_email=str(core.user_alice.email),
            variant=InvitationVariant(InvitationVariant.EDITOR),
        )

        accepted = InvitationService.accept_invitation(
            code=str(invitation.token), user=core.user_alice, access=ACCESS
        )
        assert accepted.state == InvitationState.ACCEPTED
        # The favorite is created; only the editor relation must be rejected.
        assert Favorite.objects.filter(user=core.user_alice, wishlist=core.list_alice).count() >= 1

        with pytest.raises(WishlistCollaborationOwnerAsEditorError):
            InvitationService.consent_editor(invitation=accepted, user=core.user_alice)

    def test_decline_sets_declined_without_side_effects(self, core: CoreFixture) -> None:
        """Declining sets DECLINED and creates neither favorite nor editor."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))

        declined = InvitationService.decline_invitation(
            code=str(invitation.token), user=core.user_bob, access=ACCESS
        )

        assert declined.state == InvitationState.DECLINED
        assert declined.declined_at is not None
        assert Favorite.objects.filter(user=core.user_bob, wishlist=core.list_alice).count() == 0
        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_bob)


@pytest.mark.django_db
class TestAccessMode:
    """The access mode (see req-0002, acceptance criteria "Access mode")."""

    def test_nobody_mode_blocks_acceptance(self, core: CoreFixture) -> None:
        """In NOBODY mode accepting is not possible; the invitation stays PENDING."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=CoreAccess.NOBODY
            )

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    def test_nobody_mode_blocks_decline(self, core: CoreFixture) -> None:
        """In NOBODY mode declining is not possible either (see REQ-2.42)."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationInvalidError):
            InvitationService.decline_invitation(
                code=str(invitation.token), user=core.user_bob, access=CoreAccess.NOBODY
            )

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    @freeze_time("2026-01-01 12:00:00")
    def test_nobody_mode_does_not_revoke_open_invitations(self, core: CoreFixture) -> None:
        """Open invitations survive a closed access mode and expire regularly."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)

        with pytest.raises(InvitationInvalidError):
            InvitationService.accept_invitation(
                code=str(invitation.token), user=core.user_bob, access=CoreAccess.NOBODY
            )

        # The invitation is not revoked by the mode; it simply expires after ten days.
        with freeze_time("2026-01-11 12:00:00"):
            assert WishlistInvitation.objects.get(pk=invitation.pk).state == InvitationState.EXPIRED


@pytest.mark.django_db
class TestIsSignupOpen:
    """Sign-up gating follows the configured access mode (see ADR-1000, REQ-2.39/REQ-2.42)."""

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            (CoreAccess.EXISTING, False),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_without_invitation(self, access: CoreAccess, expected: bool) -> None:
        assert InvitationService.is_signup_open(code=None, access=access) is expected

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            (CoreAccess.EXISTING, False),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_with_unknown_code(self, core: CoreFixture, access: CoreAccess, expected: bool) -> None:
        assert InvitationService.is_signup_open(code="does-not-exist", access=access) is expected

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            # In EXISTING mode the switch is off by default; even a valid invitation does not open sign-up.
            (CoreAccess.EXISTING, False),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_with_valid_invitation_and_switch_off(
        self, core: CoreFixture, access: CoreAccess, expected: bool
    ) -> None:
        invitation = _sent_invitation(core)

        assert InvitationService.is_signup_open(code=str(invitation.token), access=access) is expected

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            (CoreAccess.EXISTING, True),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_with_valid_invitation_and_switch_on(
        self, core: CoreFixture, settings: Any, access: CoreAccess, expected: bool
    ) -> None:
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)

        assert InvitationService.is_signup_open(code=str(invitation.token), access=access) is expected

    @freeze_time("2026-01-01 12:00:00")
    def test_with_expired_invitation_and_switch_on(self, core: CoreFixture, settings: Any) -> None:
        """Only PENDING invitations open sign-up; an expired one does not."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)

        with freeze_time("2026-01-15 12:00:00"):
            assert (
                InvitationService.is_signup_open(code=str(invitation.token), access=CoreAccess.EXISTING)
                is False
            )

    def test_with_accepted_invitation_and_switch_on(self, core: CoreFixture, settings: Any) -> None:
        """Only PENDING invitations open sign-up; an accepted one does not."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        assert (
            InvitationService.is_signup_open(code=str(invitation.token), access=CoreAccess.EXISTING)
            is False
        )

    def test_with_declined_invitation_and_switch_on(self, core: CoreFixture, settings: Any) -> None:
        """Only PENDING invitations open sign-up; a declined one does not."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        InvitationService.decline_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        assert (
            InvitationService.is_signup_open(code=str(invitation.token), access=CoreAccess.EXISTING)
            is False
        )

    def test_with_revoked_invitation_and_switch_on(self, core: CoreFixture, settings: Any) -> None:
        """Only PENDING invitations open sign-up; a revoked one does not."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)

        InvitationService.revoke_pending_for_wishlist(wishlist=core.list_alice)

        assert (
            InvitationService.is_signup_open(code=str(invitation.token), access=CoreAccess.EXISTING)
            is False
        )


@pytest.mark.django_db
class TestInvitationAllowsEmail:
    """Registration through an invitation only uses its invitee address (REQ-2.41)."""

    def test_matching_email(self, core: CoreFixture) -> None:
        invitation = _sent_invitation(core)

        assert (
            InvitationService.invitation_allows_email(code=str(invitation.token), email=INVITEE_EMAIL)
            is True
        )

    def test_match_is_case_insensitive(self, core: CoreFixture) -> None:
        invitation = _sent_invitation(core)

        assert (
            InvitationService.invitation_allows_email(
                code=str(invitation.token), email=INVITEE_EMAIL.upper()
            )
            is True
        )

    def test_different_email(self, core: CoreFixture) -> None:
        invitation = _sent_invitation(core)

        assert (
            InvitationService.invitation_allows_email(
                code=str(invitation.token), email="someone-else@example.com"
            )
            is False
        )

    def test_without_code(self, core: CoreFixture) -> None:
        assert InvitationService.invitation_allows_email(code=None, email=INVITEE_EMAIL) is False

    def test_without_email(self, core: CoreFixture) -> None:
        invitation = _sent_invitation(core)

        assert InvitationService.invitation_allows_email(code=str(invitation.token), email=None) is False

    def test_with_unknown_code(self, core: CoreFixture) -> None:
        assert (
            InvitationService.invitation_allows_email(code="does-not-exist", email=INVITEE_EMAIL) is False
        )
