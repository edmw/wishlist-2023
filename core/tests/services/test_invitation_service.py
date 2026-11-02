from typing import Any, Generator

import pytest
from django.core import mail
from freezegun import freeze_time

from core.models import User, Wishlist, WishlistInvitation
from core.models.types import Visibility
from core.services import (
    InvitationAlreadyAcceptedError,
    InvitationAlreadySentError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotSendableError,
    InvitationPrivateWishlistError,
    InvitationService,
)
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"


@pytest.fixture(autouse=True)
def _locmem_email(settings: Any) -> Generator[None, None, None]:
    """Ensures emails are captured in memory instead of being sent."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield
    mail.outbox = []


@pytest.mark.django_db
class TestCreateInvitation:
    def test_creates_unsent_invitation(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )

        assert invitation.pk is not None
        assert invitation.wishlist_id == core.list_alice.id
        assert invitation.inviter_id == core.user_alice.id
        assert str(invitation.invitee_email) == INVITEE_EMAIL
        assert len(str(invitation.code)) > 0
        assert invitation.sent is False
        assert invitation.accepted is False

    def test_rejects_private_wishlist(self, core: CoreFixture) -> None:
        private_list = Wishlist.objects.create(
            owner=core.user_alice,
            name_field="Private list",
            description_field="",
            visibility_field=Visibility.PRIVATE,
            item_ordering_field="+name",
        )

        with pytest.raises(InvitationPrivateWishlistError):
            InvitationService.create_invitation(
                wishlist=private_list,
                inviter=core.user_alice,
                invitee_email=INVITEE_EMAIL,
            )


@pytest.mark.django_db
class TestSendInvitation:
    def test_marks_sent_and_sends_email(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )

        InvitationService.send_invitation(invitation=invitation)

        invitation.refresh_from_db()
        assert invitation.sent is True
        assert invitation.sent_at is not None

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [INVITEE_EMAIL]
        # The email contains the invitation link with the code.
        assert str(invitation.code) in message.body
        assert f"/invitations/{invitation.code}/" in message.body

    def test_falls_back_to_username_if_no_full_name(self, core: CoreFixture) -> None:
        """The inviter’s username is used if the user has no full name set."""
        inviter = User.objects.create(username="noname", email="noname@example.com")
        assert str(inviter.full_name) == ""

        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=inviter,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation)

        message = mail.outbox[0]
        assert "noname has invited you" in message.body
        assert "The invitation was sent by noname." in message.body

    def test_raises_if_already_sent(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation)

        with pytest.raises(InvitationAlreadySentError):
            InvitationService.send_invitation(invitation=invitation)

    def test_raises_if_no_invitee_email(self, core: CoreFixture) -> None:
        invitation = _unsent_without_email(core.user_alice, core.list_alice)

        with pytest.raises(InvitationNotSendableError):
            InvitationService.send_invitation(invitation=invitation)


def _unsent_without_email(inviter: User, wishlist: Wishlist) -> WishlistInvitation:
    return WishlistInvitation.objects.create(
        inviter=inviter,
        wishlist=wishlist,
    )


@pytest.mark.django_db
class TestAcceptInvitation:
    def test_accepts_invitation(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation)

        accepted = InvitationService.accept_invitation(code=str(invitation.code), user=core.user_bob)

        assert accepted.pk == invitation.pk
        accepted.refresh_from_db()
        assert accepted.accepted is True
        assert accepted.accepted_at is not None

    def test_raises_if_not_found(self, core: CoreFixture) -> None:
        with pytest.raises(InvitationNotFoundError):
            InvitationService.accept_invitation(code="does-not-exist", user=core.user_bob)

    def test_raises_if_already_accepted(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation)

        InvitationService.accept_invitation(code=str(invitation.code), user=core.user_bob)

        with pytest.raises(InvitationAlreadyAcceptedError):
            InvitationService.accept_invitation(code=str(invitation.code), user=core.user_carol)

    @freeze_time("2026-01-01 12:00:00")
    def test_raises_if_expired(self, core: CoreFixture) -> None:
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email=INVITEE_EMAIL,
        )
        InvitationService.send_invitation(invitation=invitation)

        # Move past the configured expiry (ten days).
        with freeze_time("2026-01-15 12:00:00"):
            with pytest.raises(InvitationExpiredError):
                InvitationService.accept_invitation(code=str(invitation.code), user=core.user_bob)
