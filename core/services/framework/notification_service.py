import logging
from dataclasses import dataclass
from typing import Mapping

from django.template.loader import render_to_string

from core.models import User
from core.services.adapter import RESTClientError
from core.services.adapter.email_service import EmailService
from core.services.adapter.pushover_service import (
    PushoverService,
    PushoverServiceInvalidResponseError,
)

logger = logging.getLogger(__name__)


def render_message(
    user: User,
    template_name: str,
    html_template_name: str | None = None,
    simple_html_template_name: str | None = None,
    context: Mapping[str, object] | None = None,
) -> tuple[str, str | None, str | None]:
    if context is None:
        context = {}
    context = {
        **context,
        "user_full_name": user.full_name,
    }

    message = render_to_string(
        template_name=template_name,
        context=context,
    )

    if html_template_name:
        html_message = render_to_string(
            template_name=html_template_name,
            context=context,
        )
    else:
        html_message = None

    if simple_html_template_name:
        simple_html_message = render_to_string(
            template_name=simple_html_template_name,
            context=context,
        )
    else:
        simple_html_message = None

    return (message, html_message, simple_html_message)


@dataclass
class NotificationServiceSendResult:
    email: bool | None = None
    pushover: bool | None = None


class NotificationService:
    @staticmethod
    def send(
        *,
        user: User,
        subject: str,
        template_name: str,
        html_template_name: str | None = None,
        simple_html_template_name: str | None = None,
        context: Mapping[str, object] | None = None,
    ) -> NotificationServiceSendResult:
        result = NotificationServiceSendResult()

        subject = f"🎁 {subject}"
        message, html_message, simple_html_message = render_message(
            user,
            template_name,
            html_template_name,
            simple_html_template_name,
            context=context,
        )

        if user.settings.email_enabled:
            EmailService.send(
                user=user,
                subject=subject,
                message=message,
                html_message=html_message,
            )
            result.email = True

        if user.settings.pushover_enabled:
            if pushover_key := user.settings.pushover_key:
                try:
                    PushoverService.send(
                        user=user,
                        subject=subject,
                        message=message,
                        html_message=simple_html_message,
                        key=pushover_key,
                    )
                    result.pushover = True
                except (PushoverServiceInvalidResponseError, RESTClientError) as exc:
                    logger.exception("Failure sending Pushover notification", exc_info=exc)
                    result.pushover = False

        return result
