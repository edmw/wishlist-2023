import logging

from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_social_login)
def log_google_uid(sender, request, sociallogin, **kwargs):
    provider = sociallogin.account.provider
    if settings.ENVIRONMENT_IS_DEVELOPMENT and provider == "google":
        uid = sociallogin.account.uid
        email = sociallogin.user.email
        logger.info(f"[Allauth] Google login for {email}, uid={uid}")
