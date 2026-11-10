import datetime
import logging
from typing import Any, Mapping

from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils import timezone

from webapp.services import EmailTransportService

logger = logging.getLogger(__name__)


@receiver(pre_social_login)
def log_google_uid(
    sender: Any,
    request: HttpRequest,
    sociallogin: SocialLogin,
    **kwargs: Any,
) -> None:
    provider = sociallogin.account.provider
    if settings.ENVIRONMENT_IS_DEVELOPMENT and provider == "google":
        user = sociallogin.user
        account = sociallogin.account
        if user is None or account is None:
            return
        uid = getattr(account, "uid", None)
        email = getattr(user, "email", None)
        logger.info(f"[Allauth] Google login for {email}, uid={uid}")


@receiver(user_signed_up)
def notify_admin_on_new_signup(sender: Any, **kwargs: Any) -> None:
    """Notifies the configured administrator about a new signup.

    A plain text email is sent to `settings.WEBAPP_ADMIN_EMAIL` if
    `settings.WEBAPP_SIGNUP_NOTIFICATION_ENABLED` is enabled and an address is
    configured. Transport failures are logged but never raised so that a
    broken mail transport cannot break the signup itself.
    """
    user = kwargs.get("user")
    if not isinstance(user, AbstractUser):
        return

    if not settings.WEBAPP_SIGNUP_NOTIFICATION_ENABLED:
        return

    address = settings.WEBAPP_ADMIN_EMAIL
    if not address:
        logger.warning(
            "Signup notification is enabled but WEBAPP_ADMIN_EMAIL is not set; "
            "no notification email was sent."
        )
        return

    try:
        EmailTransportService.send_to_address(
            address=address,
            subject=_signup_notification_subject(user),
            message=_signup_notification_message(user, kwargs),
        )
    except Exception as exc:
        logger.exception("Failure sending signup notification email", exc_info=exc)


def _signup_notification_subject(user: AbstractUser) -> str:
    """Builds the subject of the signup notification email.

    Arguments:
        user: The newly registered user.

    Returns:
        The subject line, prefixed with `settings.EMAIL_SUBJECT_PREFIX`.
    """
    return f"{settings.EMAIL_SUBJECT_PREFIX}New signup: {user.username}"


def _signup_notification_message(user: AbstractUser, kwargs: Mapping[str, Any]) -> str:
    """Builds the plain text body of the signup notification email.

    Arguments:
        user: The newly registered user.
        kwargs: Keyword arguments of the `user_signed_up` signal; a
            `sociallogin` entry marks a social (e.g. Google) signup.

    Returns:
        The plain text message body.
    """
    fields: list[tuple[str, str]] = []
    if full_name := user.get_full_name():
        fields.append(("Name", full_name))
    email = getattr(user, "email", "") or "(none)"
    signed_up_at = (getattr(user, "created_at", None) or timezone.now()).astimezone(datetime.timezone.utc)
    sociallogin = kwargs.get("sociallogin")
    method = sociallogin.account.provider if isinstance(sociallogin, SocialLogin) else "email/password"
    fields.extend(
        [
            ("Username", str(user.username)),
            ("Email", email),
            ("Signed up at", f"{signed_up_at:%Y-%m-%d %H:%M} UTC"),
            ("Method", method),
        ]
    )
    body = "\n".join(f"{label + ':':<14}{value}" for label, value in fields)
    return f"A new account has been registered on {settings.WEBAPP_LOCATION}.\n" f"\n{body}\n"
