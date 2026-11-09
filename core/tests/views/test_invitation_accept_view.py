"""Tests for the invitation accept view."""

from http import HTTPStatus
from typing import Any, Generator
from urllib.parse import urlencode

import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from django.http import HttpResponseBase
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from core import constants
from core.access import CoreAccess
from core.models import User, WishlistInvitation
from core.models.types import InvitationState
from core.services import InvitationService
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"

# The baseline access mode for the view tests.
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


def _sent_invitation(core: CoreFixture) -> WishlistInvitation:
    invitation = InvitationService.create_invitation(
        wishlist=core.list_alice,
        inviter=core.user_alice,
        invitee_email=INVITEE_EMAIL,
        access=ACCESS,
    )
    InvitationService.send_invitation(invitation=invitation)
    return invitation


def _accept_url(code: str) -> str:
    return reverse(constants.VIEW_INVITATION_ACCEPT, kwargs={constants.INVITATION_CODE_KEY: code})


@pytest.mark.django_db
class TestInvitationAcceptView:
    def _messages(self, response: HttpResponseBase) -> list[str]:
        return [str(message) for message in response.context["messages"]]  # type: ignore[index]

    def test_authenticated_user_accepts_invitation(self, core: CoreFixture, client: Client) -> None:
        """A logged-in user accepts the invitation and is redirected to the list."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.FOUND
        assert response.headers["Location"] == core.list_alice.get_absolute_url()

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.ACCEPTED
        assert invitation.accepted_at is not None

    def test_authenticated_user_acceptance_shows_success_message(
        self, core: CoreFixture, client: Client
    ) -> None:
        """A success message is shown after accepting an invitation."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)), follow=True)

        assert "The invitation has been accepted." in self._messages(response)

    def test_anonymous_user_is_redirected_to_signin_page(self, core: CoreFixture, client: Client) -> None:
        """An anonymous user is sent to the invitation sign-in page with a link back to the list."""
        invitation = _sent_invitation(core)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.FOUND
        next_url = urlencode({"next": core.list_alice.get_absolute_url()})
        assert response.headers["Location"] == f"/invitations/signin/?{next_url}"

    def test_anonymous_user_has_invitation_parked_in_session(
        self, core: CoreFixture, client: Client
    ) -> None:
        """The plaintext token is parked in the session and not accepted yet."""
        invitation = _sent_invitation(core)

        client.get(_accept_url(str(invitation.token)))

        # Only a hash of the token is stored; the session carries the plaintext.
        assert client.session[constants.INVITATION_CODE_SESSION_KEY] == str(invitation.token)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    @freeze_time("2026-01-01 12:00:00")
    def test_expired_invitation_shows_error_page(self, core: CoreFixture, client: Client) -> None:
        """An expired invitation cannot be accepted any more."""
        invitation = _sent_invitation(core)

        # Move past the configured expiry (ten days).
        with freeze_time("2026-01-15 12:00:00"):
            response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.OK
        assert "This invitation has expired." in response.content.decode()

    def test_unknown_code_shows_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """An unknown code renders the invalid page with a 404 status."""
        response = client.get(_accept_url("does-not-exist"))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

    def test_already_accepted_invitation_redirects_to_list(self, core: CoreFixture, client: Client) -> None:
        """An already accepted invitation cannot be accepted again."""
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)), follow=True)

        assert "This invitation has already been accepted." in self._messages(response)
