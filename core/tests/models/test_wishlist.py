"""Tests for the wishlist model along the lines of req-0002."""

from typing import Any, Generator

import pytest
from allauth.account.models import EmailAddress
from django.core import mail

from core.access import CoreAccess
from core.models import User, Wishlist, WishlistInvitation
from core.models.types import InvitationState, Visibility
from core.services import InvitationService
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"

ACCESS = CoreAccess.EXISTING


@pytest.fixture(autouse=True)
def _locmem_email(settings: Any) -> Generator[None, None, None]:
    """Ensures emails are captured in memory instead of being sent."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield
    mail.outbox = []


def _users_list(owner: User) -> Wishlist:
    """Creates a wish list with visibility USERS owned by the given user."""
    return Wishlist.objects.create(
        owner=owner,
        name_field="Users list",
        description_field="",
        visibility_field=Visibility.USERS,
        item_ordering_field="+name",
    )


def _verified_email(user: User, email: str) -> EmailAddress:
    """Creates a verified allauth email address for the given user."""
    return EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)


def _created_invitation(
    *, wishlist: Wishlist, inviter: User, invitee_email: str = INVITEE_EMAIL
) -> WishlistInvitation:
    """Creates an invitation that has not been sent yet (state CREATED)."""
    return InvitationService.create_invitation(
        wishlist=wishlist,
        inviter=inviter,
        invitee_email=invitee_email,
        access=ACCESS,
    )


def _sent_invitation(
    *, wishlist: Wishlist, inviter: User, invitee_email: str = INVITEE_EMAIL
) -> WishlistInvitation:
    """Creates and sends an invitation; returns it in state PENDING."""
    invitation = _created_invitation(wishlist=wishlist, inviter=inviter, invitee_email=invitee_email)
    InvitationService.send_invitation(invitation=invitation)
    return invitation


@pytest.mark.django_db
class TestWishlistSaveVisibilityHook:
    """Becoming private revokes the list's open invitations (see REQ-2.27/REQ-2.29)."""

    def test_becoming_private_revokes_open_invitations(self, core: CoreFixture) -> None:
        """CREATED and PENDING invitations are revoked; final states stay untouched."""
        wishlist = _users_list(core.user_alice)
        created = _created_invitation(wishlist=wishlist, inviter=core.user_alice)
        pending = _sent_invitation(
            wishlist=wishlist, inviter=core.user_alice, invitee_email="second@example.com"
        )
        _verified_email(core.user_bob, "third@example.com")
        accepted = _sent_invitation(
            wishlist=wishlist, inviter=core.user_alice, invitee_email="third@example.com"
        )
        InvitationService.accept_invitation(code=str(accepted.token), user=core.user_bob, access=ACCESS)
        _verified_email(core.user_carol, "fourth@example.com")
        declined = _sent_invitation(
            wishlist=wishlist, inviter=core.user_alice, invitee_email="fourth@example.com"
        )
        InvitationService.decline_invitation(code=str(declined.token), user=core.user_carol, access=ACCESS)

        wishlist.visibility = Visibility(Visibility.PRIVATE)
        wishlist.save()

        created.refresh_from_db()
        pending.refresh_from_db()
        accepted.refresh_from_db()
        declined.refresh_from_db()
        assert created.state == InvitationState.REVOKED
        assert pending.state == InvitationState.REVOKED
        assert accepted.state == InvitationState.ACCEPTED
        assert declined.state == InvitationState.DECLINED

    def test_saving_a_private_list_again_does_not_change_states(self, core: CoreFixture) -> None:
        """A subsequent save of an already private list leaves the states as they are."""
        wishlist = _users_list(core.user_alice)
        pending = _sent_invitation(wishlist=wishlist, inviter=core.user_alice)

        wishlist.visibility = Visibility(Visibility.PRIVATE)
        wishlist.save()
        wishlist.name_field = "Renamed"
        wishlist.save()

        pending.refresh_from_db()
        assert pending.state == InvitationState.REVOKED

    def test_switching_between_public_and_users_keeps_open_invitations(self, core: CoreFixture) -> None:
        """Switching between the other visibilities has no effect (see REQ-2.29)."""
        wishlist = _users_list(core.user_alice)
        pending = _sent_invitation(wishlist=wishlist, inviter=core.user_alice)

        wishlist.visibility = Visibility(Visibility.PUBLIC)
        wishlist.save()
        assert WishlistInvitation.objects.get(pk=pending.pk).state == InvitationState.PENDING

        wishlist.visibility = Visibility(Visibility.USERS)
        wishlist.save()
        _verified_email(core.user_bob, INVITEE_EMAIL)
        accepted = InvitationService.accept_invitation(
            code=str(pending.token), user=core.user_bob, access=ACCESS
        )

        assert accepted.state == InvitationState.ACCEPTED

    def test_update_fields_without_visibility_does_not_revoke(self, core: CoreFixture) -> None:
        """Saving other fields only does not revoke open invitations, even if the
        in-memory visibility is private but not written to the database."""
        wishlist = _users_list(core.user_alice)
        pending = _sent_invitation(wishlist=wishlist, inviter=core.user_alice)

        wishlist.name_field = "Renamed"
        wishlist.visibility = Visibility(Visibility.PRIVATE)
        wishlist.save(update_fields=[Wishlist.Fields.NAME])

        assert Wishlist.objects.get(pk=wishlist.pk).visibility_field == Visibility.USERS
        assert WishlistInvitation.objects.get(pk=pending.pk).state == InvitationState.PENDING
