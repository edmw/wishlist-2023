"""Base class and Mixins for webapp’s commands."""

import logging
import os
from pathlib import Path
from typing import Any, Protocol

from django.apps import apps
from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError, CommandParser


class WebappBaseCommand(BaseCommand):
    """Base class for a webapp’s command.

    Provides utility functions and can be extended by Mixins.
    """

    def banner(self, lines: str | list[str], discreet: bool = False, min_width: int = 42) -> None:
        """Prints a banner with the specified text to stdout.

        Arguments:
            lines: str | list[str]
                Either a string or multiple strings which will be printed as
                banner text.
            discreet: bool
                Prints the banner with discretion.
            min_width: int
                Specifies a minimum width for the banner.
        """
        char = "#" if not discreet else "·"

        if not isinstance(lines, list):
            lines = [lines]

        longest_line_length = max(len(max(lines, key=len)), min_width)

        first_and_last_line = char * longest_line_length + char * 6

        out = ["", first_and_last_line]

        for line in lines:
            line_padded = line.center(longest_line_length)
            line_formatted = f"{char}{char} {line_padded} {char}{char}"
            out.append(line_formatted)

        out.append(first_and_last_line)
        out.append("")

        for line in out:
            self.stdout.write(line)

    def get_app_paths(self) -> list[Path]:
        """Returns a list of Paths to all apps which are part of the webapp.

        Omits all apps installed via packages.
        """
        base_path = Path(django_settings.BASE_DIR)
        app_paths = []
        for app in apps.get_app_configs():
            app_path = Path(app.path)
            if app_path.is_relative_to(base_path):
                app_paths.append(app_path)
        return app_paths

    @property
    def is_development(self) -> bool:
        """Returns True if the command is running in development environment."""
        return django_settings.ENVIRONMENT_IS_DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Returns True if the command is running in testing environment."""
        return django_settings.ENVIRONMENT_IS_TESTING

    def check_exit(self, returncode: int = 0) -> None:
        if returncode:
            raise CommandError(returncode)

    def handle(self, *args: Any, **options: Any) -> None:
        """The actual logic of the command to be implemented by subclasses."""
        ...


class BaseCommandProtocol(Protocol):
    """Protocol for command Mixins."""

    def handle(self, *args: Any, **options: Any) -> None:
        """The actual logic of the command."""
        ...


class HasArguments:
    class AddArgumentsCallable(Protocol):
        def __call__(self, parser: CommandParser) -> None:
            ...

    add_arguments: AddArgumentsCallable


class SupportsLogging(HasArguments, BaseCommandProtocol):
    """Mixin for commands which want to support logging."""

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for logging."""
        parser.add_argument(
            "--log-level",
            choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="WARNING",
            help="set log level",
        )
        super().add_arguments(parser=parser)

    def handle(self, *args: Any, **options: Any) -> None:
        """The actual logic of the command: Delegates to the super class,
        after initializing logging attributes.
        """
        log_level = logging.getLevelNamesMapping()[options["log_level"]]
        self.log_level = log_level
        self.log_level_name = logging.getLevelName(self.log_level)
        super().handle(*args, **options)


class SupportsDebugging(HasArguments, BaseCommandProtocol):
    """Mixin for commands which want to support debugging."""

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for debugging."""
        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
            help="enable debugging",
        )
        super().add_arguments(parser=parser)

    def handle(self, *args: Any, **options: Any) -> None:
        """The actual logic of the command: Delegates to the super class,
        after initializing debugging attributes.
        """
        self.enable_debugging = bool(options.get("debug", False))
        super().handle(*args, **options)

    def debugpy_listen(self) -> None:
        """Debugger will listen on port 3000 inside the container."""
        import debugpy

        # Starting the debug adapter for incoming connections.
        # SECURITY: While the app is running in a container environment,
        # we are binding intentionally on all interfaces.
        debugpy.listen(("0.0.0.0", 3000))  # nosec

    def debugpy_listen_with_wait(self) -> None:
        """Debugger will listen on port 3000 inside the container and
        wait for the Debugger client to connect.
        """
        import debugpy

        # Starting the debug adapter for incoming connections.
        # SECURITY: While the app is running in a container environment,
        # we are binding intentionally on all interfaces.
        debugpy.listen(("0.0.0.0", 3000))  # nosec
        debugpy.wait_for_client()


class SupportsAutoreloading(BaseCommandProtocol):
    """Mixin for commands which want to support auto-reloading."""

    @property
    def is_main_run(self) -> bool:
        """Autoreload is spawning a subprocess from the initial process, which
        will be restarted after any file change. This returns True if we are
        running inside the subprocess (the "main" run doing all the work) or
        False otherwise.
        """
        return "RUN_MAIN" in os.environ

    @property
    def is_initial_run(self) -> bool:
        """Autoreload is spawning a subprocess from the initial process, which
        will be restarted after any file change. This returns True if we are
        running inside the initial process or False otherwise.
        """
        return not self.is_main_run

    def handle(self, *args: Any, **options: Any) -> None:
        """The actual logic of the command: Delegates to the super class."""
        super().handle(*args, **options)
