"""Allauth integration for the Core application."""

from django.http import HttpRequest, HttpResponse

from core import constants
from core.apps import CoreConfig
from core.services import InvitationService


def signup_open(*, request: HttpRequest) -> bool:
    """Returns true if sign-up is currently open.

    Sign-up stays closed during the beta period (see ADR-1000): a new account
    can be created only on the basis of an invitation parked in the session
    that still exists and has neither expired nor been accepted already.

    Arguments:
        request: The current request whose session is inspected.

    Returns:
        True if sign-up may proceed, False otherwise.
    """
    return InvitationService.is_signup_open(
        code=request.session.get(constants.INVITATION_CODE_SESSION_KEY)
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
