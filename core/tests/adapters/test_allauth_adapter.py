"""Tests for the allauth integration of the Core application."""

from typing import Any

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest
from django.test.client import RequestFactory

from core import constants
from core.access import CoreAccess
from core.adapters.allauth import signup_open
from core.apps import CoreConfig
from core.models import WishlistInvitation
from core.services import InvitationService
from core.tests.conftest import CoreFixture


def _request(*, code: str | None) -> HttpRequest:
    request = RequestFactory().get("/")
    session: dict[str, object] = {}
    if code is not None:
        session[constants.INVITATION_CODE_SESSION_KEY] = code
    request.session = session  # type: ignore[attr-defined]
    return request


INVITEE_EMAIL = "invitee@example.com"


def _sociallogin(*, email: str | None = None, verified: bool = True) -> SocialLogin:
    """Builds a minimal social login carrying the given e-mail address."""
    addresses: list[EmailAddress] = []
    if email is not None:
        addresses.append(EmailAddress(email=email, verified=verified, primary=True))
    return SocialLogin(user=None, account=None, email_addresses=addresses)


def _sent_invitation(core: CoreFixture) -> WishlistInvitation:
    """Creates and sends an invitation for the given fixture; returns it PENDING."""
    invitation = InvitationService.create_invitation(
        wishlist=core.list_alice,
        inviter=core.user_alice,
        invitee_email=INVITEE_EMAIL,
        access=CoreAccess.EXISTING,
    )
    InvitationService.send_invitation(invitation=invitation)
    return invitation


@pytest.mark.django_db
class TestSignupOpen:
    """The policy passes the configured access mode to the service."""

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            (CoreAccess.EXISTING, False),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_without_invitation(
        self, monkeypatch: pytest.MonkeyPatch, access: CoreAccess, expected: bool
    ) -> None:
        monkeypatch.setattr(CoreConfig, "access", access)

        assert signup_open(request=_request(code=None)) is expected

    @pytest.mark.parametrize(
        ("access", "expected"),
        [
            (CoreAccess.PUBLIC, True),
            (CoreAccess.EXISTING, True),
            (CoreAccess.NOBODY, False),
        ],
    )
    def test_with_valid_invitation(
        self,
        core: CoreFixture,
        settings: Any,
        monkeypatch: pytest.MonkeyPatch,
        access: CoreAccess,
        expected: bool,
    ) -> None:
        # In the "existing" mode sign-up through an invitation is only open
        # when explicitly enabled. The invitation is created before the access
        # mode changes, as it would be in a running system.
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email="invitee@example.com",
            access=CoreAccess.EXISTING,
        )
        InvitationService.send_invitation(invitation=invitation)
        monkeypatch.setattr(CoreConfig, "access", access)

        assert signup_open(request=_request(code=str(invitation.token))) is expected

    @pytest.mark.parametrize(
        ("email", "expected"),
        [
            (INVITEE_EMAIL, True),  # exact match
            (INVITEE_EMAIL.upper(), True),  # case-insensitive
            ("someone-else@example.com", False),  # different address
        ],
    )
    def test_existing_mode_social_login_email_match(
        self,
        core: CoreFixture,
        settings: Any,
        monkeypatch: pytest.MonkeyPatch,
        email: str,
        expected: bool,
    ) -> None:
        """In EXISTING mode a social login may only register with the invited address."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.EXISTING)

        assert (
            signup_open(request=_request(code=str(invitation.token)), sociallogin=_sociallogin(email=email))
            is expected
        )

    def test_existing_mode_social_login_unverified_email(
        self, core: CoreFixture, settings: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unverified identity is rejected even when the address matches."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.EXISTING)

        assert (
            signup_open(
                request=_request(code=str(invitation.token)),
                sociallogin=_sociallogin(email=INVITEE_EMAIL, verified=False),
            )
            is False
        )

    def test_public_mode_ignores_invitation_address(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In PUBLIC mode the invitation address is not enforced on registration."""
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.PUBLIC)

        assert (
            signup_open(request=_request(code=None), sociallogin=_sociallogin(email="anyone@example.com"))
            is True
        )

    def test_nobody_mode_closes_even_with_matching_email(
        self, core: CoreFixture, settings: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In NOBODY mode no registration is possible, even with a matching address."""
        settings.INVITATION_REGISTRATION_ENABLED = True
        invitation = _sent_invitation(core)
        monkeypatch.setattr(CoreConfig, "access", CoreAccess.NOBODY)

        assert (
            signup_open(
                request=_request(code=str(invitation.token)), sociallogin=_sociallogin(email=INVITEE_EMAIL)
            )
            is False
        )
