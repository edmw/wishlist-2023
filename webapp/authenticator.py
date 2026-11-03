"""The webapp’s user authenticator."""

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest

from core.apps import CoreConfig
from core.services import InvitationService
from webapp.services import AuthLoggingService

logger = logging.getLogger(__name__)


class WebappAccountAdapter(DefaultAccountAdapter):
    """Account adapter for use with django-allauth."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Returns true only if a valid invitation to a wish list is parked in
        the session. Otherwise sign-up stays closed (closed beta)."""
        return InvitationService.get_parked_invitation(request=request) is not None


class WebappSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Social account adapter for use with django-allauth."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """Returns true only if a valid invitation to a wish list is parked in
        the session. Otherwise sign-up stays closed (closed beta).

        Overwrites `is_open_for_signup` from Account Adapter; without this
        override, sign-ups via social accounts would bypass the check above.
        """
        return InvitationService.get_parked_invitation(request=request) is not None

    def authentication_error(
        self,
        request: HttpRequest,
        provider_id: str,
        error: str | None,
        exception: Exception | None,
        extra_context: dict | None,
    ) -> None:
        """Adds detailed logging for failed authentication requests and
        returns a appropriate response if applicable.
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
        if response := CoreConfig.authentiction_error_response(request=request):
            raise ImmediateHttpResponse(response=response)
