import logging

from allauth.socialaccount.signals import pre_social_login, social_account_added
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_social_login)
def log_google_uid(sender, request, sociallogin, **kwargs):
    provider = sociallogin.account.provider
    if provider == "google":
        uid = sociallogin.account.uid
        email = sociallogin.user.email
        logger.info(f"[Allauth] Google login for {email}, uid={uid}")
