import logging
from typing import Any, cast

from allauth.account.signals import user_logged_in
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.http import HttpRequest
from django.shortcuts import redirect

from core import constants
from core.models import Language, User
from core.services import (
    InvitationAlreadyAcceptedError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationService,
)
from webapp.services import LanguageService, SignalLoggingService

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def allauth_user_logged_in_callback(sender: Any, **kwargs: Any) -> None:
    SignalLoggingService.signal_receive(
        "User logged in",
        logger=logger,
        extra={"user": kwargs.get("user")},
    )
    # Update soft language to the language set by the middleware.
    # Because this request was initially done by the anonymous user,
    # this will be the language set by the browser.
    # The soft language is determined and persisted here so that it is possible
    # to know the desired language in background tasks without having a request
    # context.
    if user := kwargs.get("user"):
        user = cast(User, user)
        language = Language(LanguageService.get_language_code())
        if user.language_soft != language:
            user.language_soft = language
            user.save(update_fields=[User.Fields.LANGUAGE_SOFT])


@receiver(user_logged_in)
def allauth_user_logged_in_accept_invitation_callback(sender: Any, **kwargs: Any) -> None:
    """Accepts an invitation parked in the session and redirects to the list.

    When an anonymous user follows an invitation link, `InvitationAcceptView`
    parks the invitation code in their session and sends them to sign in or
    sign up. This signal fires once authentication is complete — for logins of
    existing users as well as for new sign-ups — so that the parked invitation
    can be accepted automatically without the invitee having to present the
    code again (see ADR-1000).

    If no invitation is parked, or if it can no longer be accepted, this
    handler does nothing and allauth's own redirect applies.
    """
    request = kwargs.get("request")
    user = kwargs.get("user")
    if not isinstance(request, HttpRequest) or not isinstance(user, User):
        return

    code = request.session.pop(constants.INVITATION_CODE_SESSION_KEY, None)
    if not code:
        return

    try:
        invitation = InvitationService.accept_invitation(code=code, user=user)
    except (InvitationNotFoundError, InvitationExpiredError, InvitationAlreadyAcceptedError) as exc:
        logger.info(
            "Parked invitation could not be accepted after login (%s).",
            type(exc).__name__,
        )
        return

    raise ImmediateHttpResponse(response=redirect(invitation.wishlist.get_absolute_url()))


@receiver(pre_social_login)
def allauth_pre_social_login_callback(
    sender: Any, request: HttpRequest, sociallogin: SocialLogin, **kwargs: Any
) -> None:
    """Fills in the first and last name of an existing user from the data
    provided by the social account provider.

    The names are only populated if they are still empty on the local user;
    values set locally (or previously filled in) are never overwritten. This
    applies to logins of existing users, only: for new signups, django-allauth
    already populates the names during signup.

    NOTE: The names are read from the social account's extra data, not from
    `sociallogin.user`. For existing users, django-allauth's lookup replaces
    the temporary (populated) user with the database user before this signal
    is sent, so only the extra data still carries the provider's values.
    """
    SignalLoggingService.signal_receive(
        "Pre social login",
        logger=logger,
        extra={"sociallogin": sociallogin},
    )
    if not sociallogin.is_existing:
        return
    user = cast(User, sociallogin.user)
    extra_data = sociallogin.account.extra_data or {}
    update_fields: list[str] = []
    first_name = extra_data.get("given_name")
    last_name = extra_data.get("family_name")
    if not user.first_name and isinstance(first_name, str) and first_name:
        user.first_name = first_name
        update_fields.append(User.Fields.FIRST_NAME)
    if not user.last_name and isinstance(last_name, str) and last_name:
        user.last_name = last_name
        update_fields.append(User.Fields.LAST_NAME)
    if update_fields:
        user.save(update_fields=update_fields)
