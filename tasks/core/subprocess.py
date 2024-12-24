import os
import subprocess
from typing import Any

from .printer import Printer


def run(
    command: list[str],
    environment: dict[str, Any] | None = None,
    verbose: bool = False,
) -> None:
    """Runs the given command as subprocess.

    If `verbose` is false (the default), captures all output from the command
    and prints the output only if the command fails.
    If `debug` is true (default is false), prints the command and environment.
    """
    if not environment:
        environment = {}

    try:
        subprocess.run(  # nosec
            command,
            check=True,
            text=True,
            capture_output=not verbose,
            env={**os.environ.copy(), **environment},
        )
    except subprocess.CalledProcessError as cpe:
        if not verbose:
            Printer.print_boxes("OUTPUT", [("STDOUT", cpe.stdout), ("STDERR", cpe.stderr)])
        Printer.print_error("COMMAND FAILED", " ".join(command))
        raise
