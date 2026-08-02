"""Make Migrations command."""

from typing import Any

from django.core import management
from django.core.management.base import CommandParser

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Make Migrations command: Creates database migrations for all apps."""

    help = "Creates, updates or merges migration(s) for apps."

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for Make Migrations command."""
        super().add_arguments(parser=parser)

        # Flag to merge migrations.
        parser.add_argument(
            "--merge",
            default=False,
            action="store_true",
            help="merge migrations",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Creates database migrations."""
        self.banner(["WEBAPP MAKE MIGRATIONS", self.help])

        command = ["makemigrations", "--noinput"]
        if options.get("merge"):
            command.append("--merge")
        management.call_command(*command)
