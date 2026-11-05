import logging
from dataclasses import dataclass
from typing import Mapping

from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from core.models import User
from core.services.adapter import RESTClientError
from core.services.adapter.email_service import EmailService
from core.services.adapter.pushover_service import (
    PushoverService,
    PushoverServiceInvalidResponseError,
)
from webapp.services import EmailTransportService, LanguageService

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

    @staticmethod
    def send_email(
        *,
        address: str,
        subject: str,
        template_name: str,
        html_template_name: str | None = None,
        language_code: str,
        context: Mapping[str, object] | None = None,
    ) -> None:
        """Sends a templated email to an arbitrary address.

        The subject is translated and the templates are rendered in the given
        language before the message is handed over to the email transport.
        This is used for emails addressed to unregistered persons such as
        invitation recipients, where no user with notification settings exists.

        Arguments:
            address: Email address of the recipient.
            subject: Subject of the email in the default language (e.g. the
                result of `gettext_noop`), translated into the given language.
            template_name: Template for the plain text body.
            html_template_name: Optional template for the HTML alternative.
            language_code: Language code to activate while translating and
                rendering the message.
            context: Context passed to the templates.
        """
        if context is None:
            context = {}

        with LanguageService.activated(language_code=language_code):
            translated_subject = _(subject)
            message = render_to_string(
                template_name=template_name,
                context=context,
            )
            html_message = (
                render_to_string(
                    template_name=html_template_name,
                    context=context,
                )
                if html_template_name
                else None
            )

        EmailTransportService.send_to_address(
            address=address,
            subject=translated_subject,
            message=message,
            html_message=html_message,
        )
