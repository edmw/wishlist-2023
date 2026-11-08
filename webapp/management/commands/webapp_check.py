"""Check command."""

import os
import subprocess
import textwrap
from typing import Any

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Check command: Executes code checks."""

    help = (
        "Checks the webapp for bugs, programming and stylistic errors, "
        "suspicious constructs and security issues."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        """Executes a check run."""
        super().handle(*args, **options)

        self.banner(["WEBAPP CHECK", *textwrap.wrap(self.help)])

        self.banner(["Checking"], discreet=True)

        ruff_completed = subprocess.run(  # nosec
            [
                "ruff",
                "check",
                ".",
            ]
        )

        bandit_completed = subprocess.run(  # nosec
            [
                "python",
                "-W",
                "ignore::DeprecationWarning",
                "-m",
                "bandit",
                "--silent",
                "--configfile=pyproject.toml",
                "--recursive",
                ".",
            ]
        )

        # PYRIGHT_PYTHON_IGNORE_WARNINGS suppresses the wrapper’s PyPI version
        # check, keeping the run offline and its output stable.
        pyright_completed = subprocess.run(  # nosec
            [
                "pyright",
                ".",
            ],
            env={**os.environ, "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"},
        )

        returncode = (
            ruff_completed.returncode or bandit_completed.returncode or pyright_completed.returncode
        )

        self.check_exit(returncode=returncode)
