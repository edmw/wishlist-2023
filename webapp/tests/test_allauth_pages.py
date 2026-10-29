"""Tests for the page titles of allauth’s account pages.

Allauth’s views are function-based and do not populate `page_title` in the
template context. The `webapp.views.context.page_title` context processor
provides it instead, keyed by URL name. These tests guard against regressions
where a missing `page_title` would raise `VariableDoesNotExist` while
rendering `core/templates/page.html`.
"""

from http import HTTPStatus

import pytest
from django.test.client import Client, RequestFactory
from django.urls import resolve, reverse
from django.utils.translation import override

from core.models import User
from webapp.views.context import page_title


def test_page_title_processor_without_resolver_match() -> None:
    """Requests without a resolved URL (e.g. error pages) get no title."""
    request = RequestFactory().get("/accounts/login/")
    assert page_title(request) == {}


def test_page_title_processor_with_null_url_name() -> None:
    """Resolved URLs without a name (e.g. namespace-only matches) get no title."""
    from types import SimpleNamespace

    request = RequestFactory().get("/accounts/login/")
    request.resolver_match = SimpleNamespace(url_name=None)  # type: ignore[attr-defined]
    assert page_title(request) == {}


@pytest.mark.parametrize(
    ("url", "title_en"),
    [
        ("/accounts/login/", "Sign in"),
        ("/accounts/signup/", "Sign up"),
        ("/accounts/logout/", "Sign out"),
        ("/accounts/inactive/", "Account inactive"),
        ("/accounts/login/cancelled/", "Login cancelled"),
    ],
)
def test_page_title_processor_for_allauth_urls(url: str, title_en: str) -> None:
    """Allauth’s URL names are mapped to their page titles."""
    request = RequestFactory().get(url)
    request.resolver_match = resolve(url)  # type: ignore[attr-defined]
    with override("en"):
        assert page_title(request) == {"page_title": title_en}


def test_page_title_processor_for_unknown_url() -> None:
    """URLs without a mapping get no title."""
    request = RequestFactory().get("/")
    request.resolver_match = resolve("/")  # type: ignore[attr-defined]
    assert page_title(request) == {}


@pytest.mark.django_db
def test_login_page_renders_with_title(client: Client) -> None:
    """The login page renders and shows its title in the document head."""
    response = client.get(reverse("account_login"))
    assert response.status_code == HTTPStatus.OK
    content = response.content.decode()
    assert "<title>Sign in - Wishlist</title>" in content


@pytest.mark.django_db
def test_login_page_renders_with_german_title(client: Client) -> None:
    """The login page shows the translated title for German."""
    with override("de"):
        response = client.get(reverse("account_login"))
    assert response.status_code == HTTPStatus.OK
    content = response.content.decode()
    assert "<title>Anmelden - Wunschzettel</title>" in content


@pytest.mark.django_db
def test_signup_page_renders_when_closed(client: Client) -> None:
    """Sign-up is closed for anonymous users, so the signup page renders the
    closed-signup template. It must render without a `VariableDoesNotExist`
    error (the original bug reported for the Google login flow).
    """
    response = client.get(reverse("account_signup"))
    assert response.status_code == HTTPStatus.OK
    content = response.content.decode()
    assert "Wishlist</title>" in content


@pytest.mark.django_db
def test_inactive_page_renders_with_title(client: Client) -> None:
    """The inactive account page renders and shows its title."""
    response = client.get(reverse("account_inactive"))
    if response.status_code == HTTPStatus.FOUND:
        # Anonymous users are redirected to the login page.
        assert response.headers["Location"].startswith("/accounts/login/")
        follow = client.get(response.headers["Location"])
        assert follow.status_code == HTTPStatus.OK
    else:
        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert "<title>Account inactive - Wishlist</title>" in content


@pytest.mark.django_db
def test_view_context_takes_precedence_over_processor(client: Client) -> None:
    """Views that set `page_title` themselves keep precedence over the
    context processor.
    """
    from core import constants

    user = User.objects.create_user(username="precedence_test", password="S3cure-Passw0rd!")
    client.force_login(user)
    url = reverse(constants.VIEW_FAVORITES, kwargs={constants.USER_ID_KEY: user.id})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    content = response.content.decode()
    # The view’s own title (“Favorites”) must be shown, not a processor default.
    assert "<title>Favorites - Wishlist</title>" in content
