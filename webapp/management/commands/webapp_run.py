"""Run command."""
from typing import Any

from django.conf import settings as django_settings
from django.core import management

from ._base import SupportsAutoreloading, SupportsDebugging, WebappBaseCommand


class Command(SupportsDebugging, SupportsAutoreloading, WebappBaseCommand):
    """Run command: Starts the server."""

    help = "Runs the webapp."

    def handle(self, *args: Any, **options: Any) -> None:
        """Starts the server.

        Makes sure migrations are up-to-date. If debugging is enabled starts
        debugging process.
        """
        super().handle(*args, **options)

        if self.is_initial_run:
            self.banner(["WEBAPP RUN", self.help])

            self.banner(["Migrating"], discreet=True)
            command = ("wait_for_database", "--stable=1")
            management.call_command(*command)
            command = ("migrate",)
            management.call_command(*command)

            if not django_settings.DEBUG:
                self.banner(["Collecting", "static"])
                command = ("collectstatic", "--no-input")
                management.call_command(*command)

        if self.is_main_run and self.enable_debugging:
            self.banner(["Starting", "debugger"])
            self.debugpy_listen()

        # run with development webserver
        # static files are served by whitenoise
        self.banner(["Running" if self.is_main_run else "Starting"], discreet=True)
        command = ("runserver", "--nostatic", "0.0.0.0:8000")
        management.call_command(*command)
