import logging
from email.utils import formataddr

from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives

from core.models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send(
        *,
        user: User,
        subject: str,
        message: str,
        html_message: str | None,
    ) -> None:
        sender = django_settings.EMAIL_SENDER
        recipient = formataddr((user.full_name, user.email))

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=sender,
            to=[recipient],
        )
        if html_message:
            email.attach_alternative(html_message, "text/html")

        email.send()
