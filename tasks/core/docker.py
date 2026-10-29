import os
import subprocess
import sys
from typing import Protocol

from invoke.context import Context
from invoke.runners import Result

from .printer import Markup, Printer


class DockerProtocol(Protocol):
    context: Context

    def print_banner(self, title: str, message: str) -> None: ...

    def exit_with_banner(self, title: str, message: str) -> None: ...

    def run_in_context(self, command: list[str], env: dict | None = None) -> Result | None: ...

    def run_interactive(self, command: list[str], env: dict | None = None) -> None: ...


class DockerBase:

    def __init__(self, context: Context, simulation: bool = False) -> None:
        self.context = context
        self.simulation = simulation

    def print_banner(self, title: str, message: str) -> None:
        if self.simulation:
            message += f"\n{Markup.info("SIMULATION", ")")}"
        Printer.print_banner(title, message)

    def exit_with_banner(self, title: str, message: str) -> None:
        self.print_banner(title, message)
        sys.exit(1)

    def run_in_context(self, command: list[str], env: dict | None = None) -> Result | None:
        """Runs a non-interactive command via the invoke context.

        Arguments:
            command: The command to run.
            env: Additional environment variables for the command.

        Returns:
            The result of the command execution or `None` if the command was
            not executed (simulation mode).
        """
        command_string = " ".join(command)
        if self.simulation:
            Printer.simulation_would(["run command", Markup.info(command_string)])
            return None

        return self.context.run(command_string, env=env or {}, pty=True)

    def run_interactive(self, command: list[str], env: dict | None = None) -> None:
        """Runs an interactive command (e.g. `bash`, `psql`) with direct TTY access.

        Unlike `run_in_context`, the command is executed via `subprocess` instead of
        `context.run`. Invoke's PTY handling (pexpect-based) does not work reliably
        for interactive sessions, so stdin/stdout are passed through directly and
        the exit code of the command is propagated.

        Arguments:
            command: The command to run.
            env: Additional environment variables for the command.
        """
        command_string = " ".join(command)
        if self.simulation:
            Printer.simulation_would(["run interactive command", Markup.info(command_string)])
            return

        result = subprocess.run(
            command_string,
            shell=True,
            env={**os.environ, **(env or {})},
            check=False,
        )
        sys.exit(result.returncode)
