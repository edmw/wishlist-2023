"""Provides service functions for email transport."""

from email.utils import formataddr

from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives


class EmailTransportService:
    """Service class providing a collection of static functions for sending emails.

    The transport is intentionally model-agnostic: it only knows about plain
    addresses and display names, not about any application's user model.
    """

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

        The recipient does not need to be a registered user; this is used for
        emails addressed to unregistered persons such as invitation recipients.

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
