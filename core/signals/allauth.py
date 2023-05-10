import logging
from typing import Any, cast

from allauth.account.signals import user_logged_in
from django.dispatch import receiver

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
    if user := kwargs.get("user"):
        user = cast(User, user)
        language = Language(LanguageService.get_language_code())
        if user.language_soft != language:
            user.language_soft = language
            user.save(update_fields=[User.Fields.LANGUAGE_SOFT])
