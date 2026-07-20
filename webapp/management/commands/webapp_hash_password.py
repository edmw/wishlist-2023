"""Hash Password command."""

from typing import Any
from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.core.management.base import CommandParser

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Hash Password command: Create password hash for random password string."""

    help = "Creates a password hash for a given or a random password string."

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for command."""

        # Password to be hashed.
        parser.add_argument("password", nargs="?", default=str(uuid4()))

    def handle(self, *args: Any, **options: Any) -> None:
        """Makes password hash."""
        self.banner(["WEBAPP HASH PASSWORD", self.help])

        password = options["password"]
        hashed_password = make_password(password)

        self.print(hashed_password)
