import pytest
from allauth.account.signals import user_logged_in
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.signals import pre_social_login
from django.http import HttpRequest, HttpResponseRedirect
from django.test.client import RequestFactory
from django.urls import reverse

from core import constants
from core.models import User


def _sociallogin_for(user: User, *, extra_data: dict) -> SocialLogin:
    """Builds a social login for the given user with the specified account data.

    Arguments:
        user: The local user the social login points to.
        extra_data: The extra data of the social account (as provided by the provider).

    Returns:
        A social login instance, not yet sent as signal.
    """
    account = SocialAccount(provider="google", uid="123456789012345678901", extra_data=extra_data)
    return SocialLogin(user=user, account=account)


def _send_pre_social_login(sociallogin: SocialLogin) -> None:
    """Sends the pre social login signal for the given social login.

    Arguments:
        sociallogin: The social login to send the signal for.
    """
    pre_social_login.send(sender=SocialLogin, request=None, sociallogin=sociallogin)


@pytest.mark.django_db
class TestPreSocialLoginNameSync:
    def test_fills_empty_names_of_existing_user(self) -> None:
        user = User.objects.create_user(username="mib", email="mib@example.com", password=None)
        modified_at_before = user.modified_at

        sociallogin = _sociallogin_for(
            user, extra_data={"given_name": "Michael", "family_name": "Baumgärtner"}
        )
        assert sociallogin.is_existing is True

        _send_pre_social_login(sociallogin)

        user.refresh_from_db()
        assert user.first_name == "Michael"
        assert user.last_name == "Baumgärtner"
        assert str(user.full_name) == "Michael Baumgärtner"
        # Saving with update_fields must not touch the modification timestamp.
        assert user.modified_at == modified_at_before

    def test_fills_only_empty_names(self) -> None:
        user = User.objects.create_user(
            username="mib", email="mib@example.com", password=None, first_name="Michael"
        )

        sociallogin = _sociallogin_for(
            user, extra_data={"given_name": "Mike", "family_name": "Baumgärtner"}
        )

        _send_pre_social_login(sociallogin)

        user.refresh_from_db()
        assert user.first_name == "Michael"
        assert user.last_name == "Baumgärtner"

    def test_does_not_overwrite_set_names(self) -> None:
        user = User.objects.create_user(
            username="mib", email="mib@example.com", password=None, first_name="M.", last_name="B."
        )

        sociallogin = _sociallogin_for(
            user, extra_data={"given_name": "Michael", "family_name": "Baumgärtner"}
        )

        _send_pre_social_login(sociallogin)

        user.refresh_from_db()
        assert user.first_name == "M."
        assert user.last_name == "B."
        assert str(user.full_name) == "M. B."

    def test_ignores_new_signup(self) -> None:
        # A new signup carries a temporary, unsaved user instance.
        temporary_user = User(username="newbie", email="newbie@example.com")
        sociallogin = _sociallogin_for(
            temporary_user, extra_data={"given_name": "New", "family_name": "Bie"}
        )
        assert sociallogin.is_existing is False

        _send_pre_social_login(sociallogin)

        assert User.objects.filter(email="newbie@example.com").count() == 0

    def test_ignores_missing_names_in_extra_data(self) -> None:
        user = User.objects.create_user(username="mib", email="mib@example.com", password=None)

        sociallogin = _sociallogin_for(user, extra_data={"email": "mib@example.com"})

        _send_pre_social_login(sociallogin)

        user.refresh_from_db()
        assert user.first_name == ""
        assert user.last_name == ""


@pytest.mark.django_db
class TestUserLoggedInInvitationRedirect:
    """A user with a parked invitation is redirected back to the invitation page."""

    def _request(self, *, code: str | None) -> HttpRequest:
        request = RequestFactory().get("/")
        session: dict[str, object] = {}
        if code is not None:
            session[constants.INVITATION_CODE_SESSION_KEY] = code
        request.session = session  # type: ignore[attr-defined]
        return request

    def test_parked_invitation_redirects_back_to_invitation_page(self) -> None:
        user = User.objects.create_user(username="mib", email="mib@example.com", password=None)
        request = self._request(code="some-token")

        with pytest.raises(ImmediateHttpResponse) as excinfo:
            user_logged_in.send(sender=User, request=request, user=user)

        response = excinfo.value.response
        assert isinstance(response, HttpResponseRedirect)
        expected_url = reverse(
            constants.VIEW_INVITATION_ACCEPT, kwargs={constants.INVITATION_CODE_KEY: "some-token"}
        )
        assert response.url == expected_url
        # The parked code stays in the session; it is only consumed when the
        # invitation has been accepted or declined.
        assert request.session[constants.INVITATION_CODE_SESSION_KEY] == "some-token"

    def test_no_parked_invitation_does_not_redirect(self) -> None:
        user = User.objects.create_user(username="mib", email="mib@example.com", password=None)
        request = self._request(code=None)

        # No exception is raised; allauth's own redirect applies.
        user_logged_in.send(sender=User, request=request, user=user)
