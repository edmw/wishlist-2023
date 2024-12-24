from typing import Protocol

from invoke.context import Context
from invoke.runners import Result

from .printer import Markup, Printer


class DockerProtocol(Protocol):
    context: Context

    def print_banner(self, title: str, message: str) -> None: ...

    def run_in_context(self, command: list[str], env: dict | None = None) -> Result | None: ...


class DockerBase:

    def __init__(self, context: Context, simulation: bool = False) -> None:
        self.context = context
        self.simulation = simulation

    def print_banner(self, title: str, message: str) -> None:
        if self.simulation:
            message += f"\n{Markup.info("SIMULATION", ")")}"
        Printer.print_banner(title, message)

    def run_in_context(self, command: list[str], env: dict | None = None) -> Result | None:
        command_string = " ".join(command)
        if self.simulation:
            Printer.print_boxes("SIMULATION", [("COMMAND", command_string)])
        else:
            self.context.run(command_string, env=env or {}, pty=True)
