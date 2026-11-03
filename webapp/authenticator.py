"""The webapp’s generic user authenticator."""

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.conf import settings as django_settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

from webapp.services import AuthLoggingService

logger = logging.getLogger(__name__)


def _is_open_for_signup(*, request: HttpRequest) -> bool:
    """Returns true if sign-up is currently open.

    The decision is delegated to the policy configured in `SIGNUP_POLICY` (a
    dotted path to a callable taking the current request). If no policy is
    configured, sign-up stays open.
    """
    if (policy := getattr(django_settings, "SIGNUP_POLICY", None)) is None:
        return True
    return import_string(policy)(request=request)


class WebappAccountAdapter(DefaultAccountAdapter):
    """Generic account adapter for use with django-allauth."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Returns true if sign-up is currently open (see `_is_open_for_signup`)."""
        return _is_open_for_signup(request=request)


class WebappSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Generic social account adapter for use with django-allauth."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """Returns true if sign-up is currently open (see `_is_open_for_signup`).

        Overwrites `is_open_for_signup` from Account Adapter; without this
        override, sign-ups via social accounts would bypass the check above.
        """
        return _is_open_for_signup(request=request)

    def authentication_error(
        self,
        request: HttpRequest,
        provider_id: str,
        error: str | None,
        exception: Exception | None,
        extra_context: dict | None,
    ) -> None:
        """Adds detailed logging for failed authentication requests and returns
        an appropriate response if applicable.

        The response is provided by the handler configured in
        `AUTHENTICATION_ERROR_RESPONSE` (a dotted path to a callable taking the
        current request). If no handler is configured, or if it does not return
        a response, allauth’s default behavior applies.
        """
        AuthLoggingService.login_fail(
            "Social account authentication error!",
            logger=logger,
            request=request,
            provider_id=provider_id,
            error=error,
            exception=exception,
            context=extra_context,
        )
        if (handler := getattr(django_settings, "AUTHENTICATION_ERROR_RESPONSE", None)) is None:
            return
        if response := import_string(handler)(request=request):
            raise ImmediateHttpResponse(response=response)
