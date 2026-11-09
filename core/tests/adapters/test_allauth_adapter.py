"""Tests for the allauth integration of the Core application."""

import pytest
from django.http import HttpRequest
from django.test.client import RequestFactory

from core import constants
from core.access import CoreAccess
from core.adapters.allauth import signup_open
from core.apps import CoreConfig
from core.services import InvitationService
from core.tests.conftest import CoreFixture


def _request(*, code: str | None) -> HttpRequest:
    request = RequestFactory().get("/")
    session: dict[str, object] = {}
    if code is not None:
        session[constants.INVITATION_CODE_SESSION_KEY] = code
    request.session = session  # type: ignore[attr-defined]
    return request


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
        self, core: CoreFixture, monkeypatch: pytest.MonkeyPatch, access: CoreAccess, expected: bool
    ) -> None:
        monkeypatch.setattr(CoreConfig, "access", access)
        invitation = InvitationService.create_invitation(
            wishlist=core.list_alice,
            inviter=core.user_alice,
            invitee_email="invitee@example.com",
        )

        assert signup_open(request=_request(code=str(invitation.token))) is expected
