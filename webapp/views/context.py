"""Context services for views.

A set of request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.
"""
from typing import Any

from django.conf import settings as django_settings
from django.http import HttpRequest


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
