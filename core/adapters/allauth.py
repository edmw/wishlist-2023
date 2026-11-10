"""Allauth integration for the Core application."""

from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest, HttpResponse

from core import constants
from core.access import CoreAccess
from core.apps import CoreConfig
from core.services import InvitationService


def signup_open(*, request: HttpRequest, sociallogin: SocialLogin | None = None) -> bool:
    """Returns true if sign-up is currently open.

    The decision follows the configured access mode (see ADR-1000): in public
    mode sign-up is open to everyone; in existing mode only on the basis of a
    valid invitation and when registration through invitations is enabled by
    configuration; in nobody mode never. In existing mode, a social login may
    additionally only register with the verified e-mail address of the
    invitation (see REQ-2.41).

    Arguments:
        request: The current request whose session is inspected.
        sociallogin: The pending social login, if any; used to verify that the
            identity provider's e-mail matches the invited one.

    Returns:
        True if sign-up may proceed, False otherwise.
    """
    code = request.session.get(constants.INVITATION_CODE_SESSION_KEY)
    access = CoreConfig.access
    if not InvitationService.is_signup_open(code=code, access=access):
        return False
    # In existing mode a valid PENDING invitation is guaranteed by the check
    # above; a social login may only register with its invited e-mail address.
    if sociallogin is not None and access == CoreAccess.EXISTING and code:
        email = _verified_email(sociallogin=sociallogin)
        return InvitationService.invitation_allows_email(code=code, email=email)
    return True


def _verified_email(*, sociallogin: SocialLogin) -> str | None:
    """Returns a verified e-mail address of the given social login.

    The primary verified address is preferred; any other verified address is
    used as a fallback. Returns `None` if no verified address is available (see
    REQ-2.41, which requires registration to use a verified identity).

    Arguments:
        sociallogin: The pending social login whose addresses are inspected.

    Returns:
        A verified e-mail address, or `None` if none is available.
    """
    for address in sociallogin.email_addresses:
        if address.primary and address.verified:
            return address.email
    for address in sociallogin.email_addresses:
        if address.verified:
            return address.email
    return None


def authentication_error_response(*, request: HttpRequest) -> HttpResponse | None:
    """Returns the response to send when an authentication error occurred.

    Arguments:
        request: The current request.

    Returns:
        A redirect response with an explanatory error message, or `None` if no
        special response applies.
    """
    return CoreConfig.authentiction_error_response(request=request)
