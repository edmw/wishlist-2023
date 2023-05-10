"""Make Password command."""

from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import CommandParser

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Make Password command: Make password hash for given password string."""

    help = "Makes a password hash for the given password string."

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for command."""

        # Password to be hashed.
        parser.add_argument("password")

    def handle(self, *args: Any, **options: Any) -> None:
        """Makes password hash."""
        self.banner(["WEBAPP MAKE PASSWORD", self.help])

        password = options["password"]
        password_hash = make_password(password)

        print(password_hash)
