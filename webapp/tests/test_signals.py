"""Tests for the webapp’s signal handlers."""

from typing import Any, Generator

import pytest
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.core import mail

from core.models import User
from webapp.services import EmailTransportService

ADMIN_EMAIL = "admin@example.com"


@pytest.fixture(autouse=True)
def _locmem_email(settings: Any) -> Generator[None, None, None]:
    """Ensures emails are captured in memory instead of being sent."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield
    mail.outbox = []


def _send_signup(user: User, **kwargs: Any) -> None:
    """Sends the user signed up signal for the given user.

    Arguments:
        user: The newly registered user to send the signal for.
        kwargs: Additional keyword arguments of the signal (e.g. `sociallogin`).
    """
    user_signed_up.send(sender=User, request=None, user=user, **kwargs)


@pytest.mark.django_db
class TestNotifyAdminOnNewSignup:
    def test_sends_plain_text_email_when_enabled(self, settings: Any) -> None:
        settings.SIGNUP_NOTIFICATION_ENABLED = True
        settings.ADMIN_EMAIL = ADMIN_EMAIL

        user = User(username="mib", email="mib@example.com", first_name="Michael", last_name="Baumgärtner")
        _send_signup(user)

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [ADMIN_EMAIL]
        assert "New signup: mib" in message.subject
        body = message.body
        assert "Michael Baumgärtner" in body
        assert "mib@example.com" in body
        assert "email/password" in body
        # The notification is plain text only, without an HTML alternative.
        assert all(content_type != "text/html" for _, content_type in message.alternatives)

    def test_includes_provider_for_social_signups(self, settings: Any) -> None:
        settings.SIGNUP_NOTIFICATION_ENABLED = True
        settings.ADMIN_EMAIL = ADMIN_EMAIL

        user = User(username="newbie", email="newbie@example.com")
        account = SocialAccount(provider="google", uid="123456789012345678901")
        sociallogin = SocialLogin(user=user, account=account)

        _send_signup(user, sociallogin=sociallogin)

        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert "google" in body
        assert "email/password" not in body

    def test_does_not_send_when_disabled(self, settings: Any) -> None:
        settings.SIGNUP_NOTIFICATION_ENABLED = False
        settings.ADMIN_EMAIL = ADMIN_EMAIL

        user = User(username="mib", email="mib@example.com")
        _send_signup(user)

        assert len(mail.outbox) == 0

    def test_warns_when_enabled_without_address(
        self, settings: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        settings.SIGNUP_NOTIFICATION_ENABLED = True
        settings.ADMIN_EMAIL = None

        user = User(username="mib", email="mib@example.com")
        _send_signup(user)

        assert len(mail.outbox) == 0
        assert "WEBAPP_ADMIN_EMAIL" in caplog.text

    def test_transport_failure_is_swallowed(self, settings: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        settings.SIGNUP_NOTIFICATION_ENABLED = True
        settings.ADMIN_EMAIL = ADMIN_EMAIL

        def _raise(**kwargs: Any) -> None:
            raise RuntimeError("smtp down")

        monkeypatch.setattr(EmailTransportService, "send_to_address", _raise)

        user = User(username="mib", email="mib@example.com")
        # A broken mail transport must not break the signup itself.
        _send_signup(user)

        assert len(mail.outbox) == 0
