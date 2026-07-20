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
        if user is None:
            return
        uid = sociallogin.account.uid
        email = user.email
        logger.info(f"[Allauth] Google login for {email}, uid={uid}")
