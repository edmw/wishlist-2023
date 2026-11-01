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
        """Sends an email to the specified registered user.

        Arguments:
            user: Registered user who should receive the email.
            subject: Subject of the email.
            message: Plain text body of the email.
            html_message: Optional HTML alternative for the email body.
        """
        EmailService.send_to_address(
            address=user.email,
            display_name=str(user.full_name),
            subject=subject,
            message=message,
            html_message=html_message,
        )

    @staticmethod
    def send_to_address(
        *,
        address: str,
        subject: str,
        message: str,
        html_message: str | None = None,
        display_name: str | None = None,
    ) -> None:
        """Sends an email to an arbitrary email address.

        Unlike `send`, the recipient does not need to be a registered user;
        this is used for emails addressed to unregistered persons such as
        invitation recipients.

        Arguments:
            address: Email address of the recipient.
            subject: Subject of the email.
            message: Plain text body of the email.
            html_message: Optional HTML alternative for the email body.
            display_name: Optional display name shown together with the
                recipient's address.
        """
        sender = django_settings.EMAIL_SENDER
        recipient = formataddr((display_name or "", address))

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=sender,
            to=[recipient],
        )
        if html_message:
            email.attach_alternative(html_message, "text/html")

        email.send()
