import logging
from typing import Any, cast

from allauth.account.signals import user_logged_in
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse

from core import constants
from core.models import Language, User
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
def allauth_user_logged_in_invitation_redirect_callback(sender: Any, **kwargs: Any) -> None:
    """Redirects a user with a parked invitation back to the invitation page.

    When an anonymous user follows an invitation link, `InvitationAcceptView`
    parks the invitation code in their session and sends them to sign in or
    sign up. This signal fires once authentication is complete — for logins of
    existing users as well as for new sign-ups — so that the invitee is sent
    back to the invitation page, where they explicitly accept or decline (see
    ADR-1000). The parked code stays in the session; it is only consumed when
    the invitation has been accepted or declined.

    If no invitation is parked, this handler does nothing and allauth's own
    redirect applies.
    """
    request = kwargs.get("request")
    if not isinstance(request, HttpRequest):
        return

    code = request.session.get(constants.INVITATION_CODE_SESSION_KEY)
    if not code:
        return

    raise ImmediateHttpResponse(
        response=redirect(
            reverse(
                constants.VIEW_INVITATION_ACCEPT,
                kwargs={constants.INVITATION_CODE_KEY: str(code)},
            )
        )
    )


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
