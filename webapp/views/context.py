"""Context services for views.

A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.
"""

from typing import Any

from django.conf import settings as django_settings
from django.http import HttpRequest
from django.utils.translation import gettext_noop


def page_title(request: HttpRequest) -> dict[str, Any]:
    """Context request processor that provides the page title for pages whose
    views do not populate it themselves (e.g. allauth’s account pages).
    """
    titles = {
        "account_login": gettext_noop("Sign in"),
        "account_signup": gettext_noop("Sign up"),
        "socialaccount_signup": gettext_noop("Sign up"),
        "account_logout": gettext_noop("Sign out"),
        "account_inactive": gettext_noop("Account inactive"),
        "socialaccount_login_cancelled": gettext_noop("Login cancelled"),
    }
    resolver_match = request.resolver_match
    if resolver_match is None or resolver_match.url_name is None:
        return {}
    title = titles.get(resolver_match.url_name)
    if title is None:
        return {}
    return {"page_title": title}


def settings(request: HttpRequest) -> dict[str, Any]:
    """Context request processor that provides the webapp’s settings."""
    from webapp.services import LanguageService

    return {
        "webapp": {
            "VERSION": django_settings.VERSION,
            "ADMIN_SITE_ENABLED": django_settings.ADMIN_SITE_ENABLED,
            "LANGUAGES": django_settings.LANGUAGES,
            "LANGUAGE_CODE": LanguageService.get_language_code(),
            "LANGUAGE_BIDI": LanguageService.get_language_bidi(),
        }
    }
