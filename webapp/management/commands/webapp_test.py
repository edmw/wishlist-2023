"""Test command."""
import subprocess
from typing import Any

import pytest
from django.core import management
from django.core.management.base import CommandParser

from ._base import SupportsDebugging, WebappBaseCommand


class Command(SupportsDebugging, WebappBaseCommand):
    """Test command: Executes test runs."""

    help = "Tests the webapp."

    def add_arguments(self, parser: CommandParser) -> None:
        """Adds arguments for Test command."""
        super().add_arguments(parser=parser)

        # Flag to enable coverage reporting.
        parser.add_argument(
            "--coverage",
            default=False,
            action="store_true",
            help="enable coverage reporting",
        )

        # List of packages or modules to test.
        parser.add_argument("spec", nargs="*")

    def handle(self, *args: Any, **options: Any) -> None:
        """Executes a test run.

        Use `spec` option to specify which packages or modules to test. If
        omitted runs all tests.

        Makes sure migrations are up-to-date. If debugging is enabled waits for
        a debugger to connect before starting the test run.
        """
        super().handle(*args, **options)

        self.banner(["WEBAPP TEST", self.help])

        self.banner(["Migrating"], discreet=True)
        command = ("wait_for_database", "-v=0", "--stable=0")
        management.call_command(*command)
        command = ("migrate", "-v=0")
        management.call_command(*command)

        if self.enable_debugging:
            self.banner(["Waiting", "for debugger to connect"])
            self.debugpy_listen_with_wait()

        self.banner(["Testing"], discreet=True)

        # Code to test:
        spec = options.get("spec") or ["core", "core_health", "webapp"]

        arguments = []
        if options.get("coverage", False):
            # No coverage reporting if test run fails.
            arguments += ["--no-cov-on-fail"]
            # Coverage reporting to terminal.
            arguments += ["--cov-report=term"]
            # Coverage reporting to HTML.
            arguments += ["--cov-report=html"]
            # Code to cover corresponds to code to test.
            arguments += [f"--cov={s}" for s in spec]
            # Record coverage data for each test individually.
            arguments += ["--cov-context=test"]
            # Ignore deprecation warnings.
            arguments += ["-W", "ignore::DeprecationWarning"]
        arguments += spec

        if options.get("coverage", False):
            # Tests with coverage reporting must be run as a subprocess, so
            # that modules that have already been imported are also covered.
            pytest_completed = subprocess.run(["pytest"] + arguments)  # nosec
            pytest_returncode = pytest_completed.returncode
        else:
            # Run tests.
            pytest_returncode = pytest.main(arguments)

        self.check_exit(returncode=pytest_returncode)
