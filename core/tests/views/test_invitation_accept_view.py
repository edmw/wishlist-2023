"""Tests for the invitation accept view."""

import re
from http import HTTPStatus
from typing import Any, Generator

import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from django.http import HttpResponseBase
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from core import constants
from core.access import CoreAccess
from core.apps import CoreConfig
from core.models import User, WishlistInvitation
from core.models.types import InvitationState, InvitationVariant, Visibility
from core.services import FavoriteService, InvitationService, WishlistCollaborationService
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


def _sent_invitation(core: CoreFixture, *, variant: InvitationVariant | None = None) -> WishlistInvitation:
    """Creates and sends an invitation; returns it in state PENDING."""
    kwargs: dict[str, Any] = {}
    if variant is not None:
        kwargs["variant"] = variant
    invitation = InvitationService.create_invitation(
        wishlist=core.list_alice,
        inviter=core.user_alice,
        invitee_email=INVITEE_EMAIL,
        access=ACCESS,
        **kwargs,
    )
    InvitationService.send_invitation(invitation=invitation)
    return invitation


def _accept_url(code: str) -> str:
    return reverse(constants.VIEW_INVITATION_ACCEPT, kwargs={constants.INVITATION_CODE_KEY: code})


def _without_nonce(content: bytes) -> bytes:
    """Removes the per-request CSP nonces so that two rendered pages can be
    compared for identical content."""
    return re.sub(rb'nonce="[^"]+"', b'nonce=""', content)


@pytest.mark.django_db
class TestInvitationAcceptViewAnonymousGet:
    """An anonymous visitor sees only the sign-in request for a valid link and
    one identical invalid page for every other case (see REQ-2.21/REQ-2.22)."""

    def test_valid_link_redirects_to_signin_page_without_details(
        self, core: CoreFixture, client: Client
    ) -> None:
        """An anonymous user with a valid link is sent to the sign-in page; no
        list details are revealed and the code is parked in the session."""
        invitation = _sent_invitation(core)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.FOUND
        # No "next" parameter carrying the wish list (see REQ-2.21).
        assert response.headers["Location"] == reverse(constants.VIEW_INVITATION_SIGNIN)
        assert core.list_alice.get_absolute_url() not in str(response.headers["Location"])

    def test_valid_link_parks_code_in_session(self, core: CoreFixture, client: Client) -> None:
        """The plaintext token is parked in the session and not accepted yet."""
        invitation = _sent_invitation(core)

        client.get(_accept_url(str(invitation.token)))

        # Only a hash of the token is stored; the session carries the plaintext.
        assert client.session[constants.INVITATION_CODE_SESSION_KEY] == str(invitation.token)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    def test_unknown_link_renders_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """An unknown code renders the invalid page with a 404 status."""
        response = client.get(_accept_url("does-not-exist"))

        assert response.status_code == HTTPStatus.NOT_FOUND
        content = response.content.decode()
        assert "This invitation is not valid." in content
        assert core.list_alice.name not in content

    def test_expired_link_renders_identical_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """An expired link renders the same page as an unknown one (see REQ-2.22)."""
        reference = client.get(_accept_url("does-not-exist"))

        with freeze_time("2026-01-01 12:00:00"):
            invitation = _sent_invitation(core)

        # Move past the configured expiry (ten days).
        with freeze_time("2026-01-15 12:00:00"):
            response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == reference.status_code
        # The per-request CSP nonces differ; compare the content without them.
        assert _without_nonce(response.content) == _without_nonce(reference.content)


@pytest.mark.django_db
class TestInvitationAcceptViewUsedAndRevokedLinks:
    """A used or revoked link renders the same page as an unknown one
    (see REQ-2.22)."""

    def test_used_link_renders_identical_invalid_page(self, core: CoreFixture, client: Client) -> None:
        reference = client.get(_accept_url("does-not-exist"))
        _verified_email(core.user_bob, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        InvitationService.accept_invitation(code=str(invitation.token), user=core.user_bob, access=ACCESS)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == reference.status_code
        # The per-request CSP nonces differ; compare the content without them.
        assert _without_nonce(response.content) == _without_nonce(reference.content)

    def test_revoked_link_renders_identical_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A link replaced by a newer invitation is invalid (see REQ-2.10)."""
        reference = client.get(_accept_url("does-not-exist"))
        old_invitation = _sent_invitation(core)
        _sent_invitation(core)

        response = client.get(_accept_url(str(old_invitation.token)))

        assert response.status_code == reference.status_code
        # The per-request CSP nonces differ; compare the content without them.
        assert _without_nonce(response.content) == _without_nonce(reference.content)


@pytest.mark.django_db
class TestInvitationAcceptViewAuthenticatedGet:
    """A signed-in user whose verified address matches sees the action page;
    every other case gets the invalid page (see REQ-2.18/REQ-2.20)."""

    def test_matching_address_sees_action_page(self, core: CoreFixture, client: Client) -> None:
        """The action page offers explicit accept and decline actions."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert core.list_alice.name in content
        assert core.user_alice.username in content
        assert 'name="action" value="accept"' in content
        assert 'name="action" value="decline"' in content

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    def test_mismatched_address_gets_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A user whose verified address does not match cannot act (see REQ-2.18)."""
        _verified_email(core.user_carol, "other@example.com")
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

    def test_unverified_address_gets_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A matching address that the identity provider has not verified is rejected."""
        EmailAddress.objects.create(user=core.user_carol, email=INVITEE_EMAIL, verified=False, primary=True)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

    def test_nobody_mode_gets_invalid_page(
        self, core: CoreFixture, client: Client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In nobody mode even a matching user cannot act (see REQ-2.42)."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.NOBODY)

        response = client.get(_accept_url(str(invitation.token)))

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.PENDING

    def test_private_wishlist_gets_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A list that became private cannot be accepted any more (see REQ-2.31)."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        original_visibility = core.list_alice.visibility_field
        try:
            core.list_alice.visibility_field = Visibility.PRIVATE
            core.list_alice.save()

            response = client.get(_accept_url(str(invitation.token)))

            assert response.status_code == HTTPStatus.NOT_FOUND
            assert "This invitation is not valid." in response.content.decode()
        finally:
            # The fixture instance is shared across the whole session; restore its state.
            core.list_alice.visibility_field = original_visibility
            core.list_alice.save()


@pytest.mark.django_db
class TestInvitationAcceptViewPost:
    """The invitation is only acted upon by the explicit POST actions."""

    def _messages(self, response: HttpResponseBase) -> list[str]:
        return [str(message) for message in response.context["messages"]]  # type: ignore[index]

    def test_accept_notify_adds_favorite_and_redirects_to_list(
        self, core: CoreFixture, client: Client
    ) -> None:
        """Accepting a NOTIFY invitation adds the list to the favorites."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.post(_accept_url(str(invitation.token)), data={"action": "accept"}, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert response.redirect_chain[0][0] == core.list_alice.get_absolute_url()
        assert "The invitation has been accepted." in self._messages(response)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.ACCEPTED
        assert FavoriteService.is_favorite(wishlist=core.list_alice, user=core.user_carol)
        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_carol)

    def test_accept_editor_shows_consent_page(self, core: CoreFixture, client: Client) -> None:
        """Accepting an EDITOR invitation adds the favorite and offers the editor
        role as a separate consent step (see REQ-2.34)."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))
        client.force_login(core.user_carol)

        response = client.post(_accept_url(str(invitation.token)), data={"action": "accept"})

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert 'name="action" value="consent"' in content
        assert core.list_alice.name in content

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.ACCEPTED
        assert FavoriteService.is_favorite(wishlist=core.list_alice, user=core.user_carol)
        # The editor role is only granted by the explicit consent afterwards.
        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_carol)

    def test_consent_makes_user_editor(self, core: CoreFixture, client: Client) -> None:
        """The explicit consent grants the editor role (see REQ-2.34/REQ-2.44)."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))
        client.force_login(core.user_carol)

        client.post(_accept_url(str(invitation.token)), data={"action": "accept"})
        response = client.post(_accept_url(str(invitation.token)), data={"action": "consent"}, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert response.redirect_chain[0][0] == core.list_alice.get_absolute_url()
        assert "You are now an editor of the wish list." in self._messages(response)
        assert WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_carol)

    def test_consent_by_owner_is_rejected(self, core: CoreFixture, client: Client) -> None:
        """The owner of a wish list can never become its editor (see REQ-2.35)."""
        _verified_email(core.user_alice, INVITEE_EMAIL)
        invitation = _sent_invitation(core, variant=InvitationVariant(InvitationVariant.EDITOR))
        client.force_login(core.user_alice)

        client.post(_accept_url(str(invitation.token)), data={"action": "accept"})
        response = client.post(_accept_url(str(invitation.token)), data={"action": "consent"})

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert "You cannot become an editor of this wish list, because you are its owner." in content
        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_alice)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.ACCEPTED

    def test_decline_sets_state_and_creates_no_relations(self, core: CoreFixture, client: Client) -> None:
        """Declining sets the state to DECLINED without favorite or editor."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.post(_accept_url(str(invitation.token)), data={"action": "decline"}, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert response.redirect_chain[0][0] == "/"
        assert "The invitation has been declined." in self._messages(response)

        invitation.refresh_from_db()
        assert invitation.state == InvitationState.DECLINED
        assert not FavoriteService.is_favorite(wishlist=core.list_alice, user=core.user_carol)
        assert not WishlistCollaborationService.is_editor(wishlist=core.list_alice, user=core.user_carol)

    def test_post_with_unknown_code_gets_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A POST for an unknown code renders the invalid page (see REQ-2.22)."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        client.force_login(core.user_carol)

        response = client.post(_accept_url("does-not-exist"), data={"action": "accept"})

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

    def test_post_with_unknown_action_gets_invalid_page(self, core: CoreFixture, client: Client) -> None:
        """A POST with an action the form does not offer renders the invalid page."""
        _verified_email(core.user_carol, INVITEE_EMAIL)
        invitation = _sent_invitation(core)
        client.force_login(core.user_carol)

        response = client.post(_accept_url(str(invitation.token)), data={"action": "bogus"})

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "This invitation is not valid." in response.content.decode()

    def test_anonymous_post_raises_bad_request(self, core: CoreFixture, client: Client) -> None:
        """Acting on an invitation requires an authenticated user."""
        invitation = _sent_invitation(core)

        response = client.post(_accept_url(str(invitation.token)), data={"action": "accept"})

        assert response.status_code == HTTPStatus.BAD_REQUEST
