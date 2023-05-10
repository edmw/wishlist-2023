"""Make Migrations command."""

from typing import Any

from django.core import management

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Make Migrations command: Creates database migrations for all apps."""

    help = "Creates migration(s) for apps."

    def handle(self, *args: Any, **options: Any) -> None:
        """Creates database migrations."""
        self.banner(["WEBAPP MAKE MIGRATIONS", self.help])

        command = ("makemigrations",)
        management.call_command(*command)
