import logging
from typing import Any

from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from django.dispatch import receiver
from django.http import HttpRequest

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
