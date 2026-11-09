"""Tests for the invitation sign-in view."""

from http import HTTPStatus
from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse

from core import constants
from core.access import CoreAccess
from core.apps import CoreConfig
from core.models import WishlistInvitation
from core.services import InvitationService
from core.tests.conftest import CoreFixture

INVITEE_EMAIL = "invitee@example.com"


def _signin_url() -> str:
    return reverse(constants.VIEW_INVITATION_SIGNIN)


def _created_invitation(core: CoreFixture) -> WishlistInvitation:
    return InvitationService.create_invitation(
        wishlist=core.list_alice,
        inviter=core.user_alice,
        invitee_email=INVITEE_EMAIL,
    )


def _park_invitation(client: Client, invitation: WishlistInvitation) -> None:
    """Parks the plaintext token in the session, as `InvitationAcceptView` does."""
    session = client.session
    session[constants.INVITATION_CODE_SESSION_KEY] = str(invitation.token)
    session.save()


@pytest.mark.django_db
class TestInvitationSigninView:
    def test_shows_invitation_context_for_parked_invitation(
        self, core: CoreFixture, client: Client
    ) -> None:
        """An invitee with a parked invitation sees the list name and no restriction notice."""
        _park_invitation(client, _created_invitation(core))

        response = client.get(f"{_signin_url()}?{urlencode({'next': core.list_alice.get_absolute_url()})}")

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert 'You have been invited to "Wishes for Alice"' in content
        assert "Please sign in or create an account to accept the invitation." in content
        assert f'name="next" value="{core.list_alice.get_absolute_url()}"' in content
        assert 'id="google-signin"' in content
        assert "restricted to returning users" not in content

    def test_shows_generic_content_without_parked_invitation(self, client: Client) -> None:
        """A user without a parked invitation sees the generic sign-in page."""
        response = client.get(_signin_url())

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        # The default access mode is "existing".
        assert "restricted to returning users" in content
        assert 'id="google-signin"' in content

    def test_shows_restriction_notice_when_nobody_has_access(
        self, core: CoreFixture, client: Client, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In nobody mode even an invited user cannot sign up and sees the restriction notice."""
        _park_invitation(client, _created_invitation(core))
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.NOBODY)

        response = client.get(_signin_url())

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert "unable to perform any sign ins" in content
        assert 'id="google-signin"' not in content
