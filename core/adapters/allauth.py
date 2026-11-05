"""Allauth integration for the Core application."""

from django.http import HttpRequest, HttpResponse

from core import constants
from core.apps import CoreConfig
from core.services import InvitationService


def signup_open(*, request: HttpRequest) -> bool:
    """Returns true if sign-up is currently open.

    The decision follows the configured access mode (see ADR-1000): without a
    valid invitation parked in the session, sign-up is open only in public
    mode; with one, it stays closed unless nobody has been granted access at
    all.

    Arguments:
        request: The current request whose session is inspected.

    Returns:
        True if sign-up may proceed, False otherwise.
    """
    return InvitationService.is_signup_open(
        code=request.session.get(constants.INVITATION_CODE_SESSION_KEY),
        access=CoreConfig.access,
    )


def authentication_error_response(*, request: HttpRequest) -> HttpResponse | None:
    """Returns the response to send when an authentication error occurred.

    Arguments:
        request: The current request.

    Returns:
        A redirect response with an explanatory error message, or `None` if no
        special response applies.
    """
    return CoreConfig.authentiction_error_response(request=request)
