"""Migrate command."""
from typing import Any

from django.core import management

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Migrate command: Runs database migrations."""

    help = "Runs database migrations."

    def handle(self, *args: Any, **options: Any) -> None:
        """Runs database migrations.

        Waits for database to be ready before running the migrations.
        """
        self.banner(["WEBAPP MIGRATE", self.help])

        self.banner(["Migrating"], discreet=True)
        command = ("wait_for_database", "--stable=1")
        management.call_command(*command)
        command = ("migrate",)
        management.call_command(*command)
