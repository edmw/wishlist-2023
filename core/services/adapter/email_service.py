"""Email service for sending emails to registered users.

This is the domain-facing email service of the Core: it translates a user
into an address and display name and delegates the actual transport to the
framework-bound `EmailTransportService` of the webapp.
"""

from core.models.user import User
from webapp.services import EmailTransportService


class EmailService:
    """Email service for sending emails to registered users."""

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
        EmailTransportService.send_to_address(
            address=user.email,
            display_name=str(user.full_name),
            subject=subject,
            message=message,
            html_message=html_message,
        )
