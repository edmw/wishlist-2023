"""Create user command."""

from typing import Any

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.conf import settings
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, CommandParser

from core.models import User
from core.services import UserService

from ._base import CoreBaseCommand


class Command(CoreBaseCommand):
    """Creates a user by email address.

    The user is created without a usable password (social login only). By
    default, the username is derived from the local part of the email address
    and can be overridden with an explicit name. By default, the email address
    is registered as verified and primary. If a Google ID is specified, a
    Google social account is linked to the user.
    """

    help = "Creates a user by email address."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "email",
            metavar="EMAIL",
            help="Email address of the new user.",
        )
        parser.add_argument(
            "--username",
            metavar="NAME",
            help=(
                "Username for the new user. If omitted, the username is derived "
                "from the local part of the email address."
            ),
        )
        parser.add_argument(
            "--google-id",
            metavar="ID",
            help=("Google user ID to link as social account. If omitted, no " "social account is created."),
        )
        parser.add_argument(
            "--skip-email-verification",
            action="store_true",
            help="Do not register the email address as verified.",
        )

        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        super().handle(*args, **options)

        email = options.get("email")
        username = options.get("username")
        google_id = options.get("google_id")
        skip_email_verification = options.get("skip_email_verification", False)

        if not email:
            raise CommandError("Email address is required.")

        existing_user = UserService.find_user_for_email(email=email)
        if existing_user is not None:
            raise CommandError(f"A user with the email '{email}' already exists (ID {existing_user.id}).")

        existing_account = None
        if google_id:
            existing_account = SocialAccount.objects.filter(provider="google", uid=google_id).first()
            if existing_account is not None:
                raise CommandError(
                    f"A Google social account with the ID '{google_id}' already exists "
                    f"(linked to user {existing_account.user.email})."
                )

        if username is not None:
            self.validate_username(username=username)
        else:
            username = self.derive_username(email=email)

        user = User.objects.create_user(username=username, email=email, password=None)

        if skip_email_verification:
            self.print(
                f"Created user {user.email} (username '{user.username}') without email verification."
            )
        else:
            EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
            self.print(
                f"Created user {user.email} (username '{user.username}') with a verified email address."
            )

        if google_id:
            if not SocialApp.objects.filter(provider="google").exists():
                self.print("Note: No Google social app is configured for this environment.")
            extra_data = {"id": google_id, "email": email, "verified_email": True}
            SocialAccount.objects.create(user=user, provider="google", uid=google_id, extra_data=extra_data)
            self.print(f"Linked Google account '{google_id}' to user {user.email}.")

    def validate_username(self, *, username: str) -> None:
        """Validates an explicitly specified username.

        Raises a `CommandError` if the name is invalid, blacklisted or already
        taken. Unlike derived names, explicit names are never modified.

        Arguments:
            username: The username to validate.
        """
        try:
            UnicodeUsernameValidator()(username)
        except ValidationError as error:
            raise CommandError(f"Invalid username '{username}': {error.messages[0]}") from error

        if username.lower() in {name.lower() for name in settings.ACCOUNT_USERNAME_BLACKLIST}:
            raise CommandError(f"The username '{username}' is reserved and cannot be used.")

        existing_user = UserService.find_user_for_username(username=username)
        if existing_user is not None:
            raise CommandError(
                f"A user with the username '{username}' already exists (ID {existing_user.id})."
            )

    def derive_username(self, *, email: str) -> str:
        """Derives a unique username from the local part of an email address.

        The local part is reduced to characters accepted by the username
        validator. If the result is empty, 'user' is used as fallback. Names
        which are blacklisted or already taken get a numeric suffix appended
        until the name is available.

        Arguments:
            email: The email address to derive the username from.

        Returns:
            A unique username.
        """
        local_part = email.split("@", 1)[0]
        sanitized = "".join(
            char for char in local_part if (char.isascii() and char.isalnum()) or char in ".@+/-_"
        )[:150]
        base = sanitized or "user"

        blacklist = {name.lower() for name in settings.ACCOUNT_USERNAME_BLACKLIST}

        candidate = base
        suffix = 2
        while True:
            if (
                candidate.lower() not in blacklist
                and UserService.find_user_for_username(username=candidate) is None
            ):
                return candidate
            candidate = f"{base[: 150 - len(str(suffix))]}{suffix}"
            suffix += 1
