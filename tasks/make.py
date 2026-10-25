import re
import tempfile
from pathlib import Path

from invoke.context import Context
from packaging.version import InvalidVersion, Version
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import run_in_context, task, task_banner
from .core.files import FilesCleaner
from .core.printer import Markup, Printer, console
from .core.project import CONFIGURATION

# region ⭐ Make Tasks ⭐


def run_pip(context: Context, arguments: list[str]) -> None:
    run_in_context(
        context,
        [
            "python -m pip",
            "--require-virtualenv",
            "--quiet",
            *arguments,
        ],
    )


def run_piptools_compile(context: Context, arguments: list[str]) -> None:
    run_in_context(
        context,
        [
            "python -m piptools",
            "compile",
            "--quiet",
            "--resolver=backtracking",
            "--generate-hashes",
            "--strip-extras",
            "--allow-unsafe",
            *arguments,
        ],
    )


def run_piptools_sync(context: Context, arguments: list[str]) -> None:
    run_in_context(
        context,
        [
            "python -m piptools",
            "sync",
            "--quiet",
            *arguments,
        ],
    )


def _parse_requirements(text: str) -> dict[str, str]:
    """Parses pip-compile output into a mapping of package name to version."""
    requirements: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==(.+)$", line)
        if not match:
            continue
        name, version = match.groups()
        requirements[name.lower()] = version.split(";")[0].removesuffix("\\").strip()
    return requirements


def _diff_requirements(
    current: dict[str, str], updated: dict[str, str]
) -> list[tuple[str, str | None, str | None]]:
    """Computes the differences between two requirement mappings.

    Returns a sorted list of (name, current_version, updated_version) tuples
    for every package that was added, removed or changed. A version of `None`
    marks an added (current is None) or removed (updated is None) package.
    """
    return [
        (name, current.get(name), updated.get(name))
        for name in sorted(set(current) | set(updated))
        if current.get(name) != updated.get(name)
    ]


def _preview_update(
    context: Context, printer: Printer, output_file: Path, compile_args: list[str]
) -> None:
    """Runs pip-compile into a temporary file and prints which dependencies
    would be added, removed or changed. The actual requirements file is not
    modified."""
    base_command = [
        "python -m piptools",
        "compile",
        "--quiet",
        "--resolver=backtracking",
        "--generate-hashes",
        "--strip-extras",
        "--allow-unsafe",
        *compile_args,
    ]

    if context.config.get("simulation", False):
        command = [*base_command, "-o", "<temporary file>", "pyproject.toml"]
        Printer.simulation_would(["run command", Markup.info(" ".join(command))])
        return

    with printer.spinner():
        with tempfile.TemporaryDirectory(prefix="wishlist-preview-") as tmp_dir:
            preview_file = Path(tmp_dir) / "requirements-preview.txt"
            command = [*base_command, "-o", str(preview_file), "pyproject.toml"]
            context.run(" ".join(command), hide=True)
            updated = _parse_requirements(preview_file.read_text())

    current = _parse_requirements(output_file.read_text())
    diff = _diff_requirements(current, updated)

    if not diff:
        message = (
            f"[dim]All dependencies in {Markup.info(output_file.name)} "
            f"are up-to-date — nothing to update.[/dim]"
        )
        console.print(message)
        return

    table = Table(box=box.MINIMAL)
    table.add_column("Package")
    table.add_column("Current", justify="right")
    table.add_column("New", justify="right")
    for name, old_version, new_version in diff:
        if old_version is None:
            # Package was added; _diff_requirements never yields (None, None).
            assert new_version is not None
            current_cell = "[dim](new)[/dim]"
            new_cell = Markup.ok(new_version)
        elif new_version is None:
            current_cell = old_version
            new_cell = Markup.not_ok("(removed)")
        else:
            try:
                upgrade = Version(new_version) > Version(old_version)
                downgrade = Version(new_version) < Version(old_version)
            except InvalidVersion:
                upgrade = downgrade = False
            if downgrade:
                new_cell = Markup.problematic(new_version)
            elif upgrade:
                new_cell = Markup.ok(new_version)
            else:
                new_cell = new_version
            current_cell = old_version
        table.add_row(name, current_cell, new_cell)

    console.print()
    console.print(
        Panel.fit(
            table,
            title=Text(f"Would update dependencies in {output_file.name}", style="white on black"),
            style="white on black",
        ),
    )
    console.print()
    console.print(
        f"[dim]Preview only — no files were modified. "
        f"Re-run with {Markup.info('--apply')} to apply the updates.[/dim]"
    )


@task()
@task_banner("🧹🧹🧹", "Cleaning\nProject")
def clean(context: Context) -> None:
    """Cleans up files and directories."""
    simulation = context.config.get("simulation", False)

    cleaner = FilesCleaner(simulation)

    printer = Printer()
    with printer.enumerator() as enumerator:

        enumerator.do("Removing files")
        enumerator.do("Removing .coverage files")
        cleaner.remove_files_in_directory(CONFIGURATION.project_paths.REPORTS_COVERAGE_HTML)
        enumerator.done()

        enumerator.do("Removing caches")
        enumerator.do("Removing .cache directory")
        cleaner.remove_directory(CONFIGURATION.project_paths.PROJECT / ".cache")
        enumerator.do("Removing __pycache__ directories")
        cleaner.find_and_remove_in_directory("__pycache__", CONFIGURATION.project_paths.PROJECT)
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Installing\nDevelopment Dependencies")
def install_development(context: Context) -> None:
    """Installs development dependencies from requirements file for development into virtual environment."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        enumerator.do("Installing development dependencies")
        with printer.spinner():
            run_pip(
                context,
                [
                    "install",
                    "--upgrade",
                    "-r requirements.txt",
                    "-r requirements-development.txt",
                ],
            )
        enumerator.done()

        enumerator.do("Checking installed dependencies")
        run_in_context(context, ["python", "-m pip", "--require-virtualenv", "--quiet check"])
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Installing\nProduction Dependencies")
def install_production(context: Context) -> None:
    """Installs production dependencies from requirements file into virtual environment."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        enumerator.do("Installing production dependencies")
        with printer.spinner():
            run_pip(
                context,
                [
                    "install",
                    "--upgrade",
                    "-r requirements.txt",
                ],
            )
        enumerator.done()

        enumerator.do("Checking installed dependencies")
        run_in_context(context, ["python", "-m pip", "--require-virtualenv", "--quiet check"])
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Syncing\nDevelopment Dependencies")
def sync_development(context: Context) -> None:
    """Syncs development dependencies from requirements file for development into virtual environment."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        enumerator.do("Syncing development dependencies")
        with printer.spinner():
            run_piptools_sync(
                context,
                [
                    "requirements.txt",
                    "requirements-development.txt",
                ],
            )
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Syncing\nProduction Dependencies")
def sync_production(context: Context) -> None:
    """Syncs production dependencies from requirements file into virtual environment."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        enumerator.do("Syncing production dependencies")
        with printer.spinner():
            run_piptools_sync(
                context,
                [
                    "requirements.txt",
                ],
            )
        enumerator.done()


def _development_compile_args(update: bool) -> list[str]:
    return [
        *["--upgrade"] * update,
        "--extra build",
        "--extra test",
        "--extra check",
        "--extra tool",
        "--extra support",
    ]


def _production_compile_args(update: bool) -> list[str]:
    return [*["--upgrade"] * update]


def _pin_or_update_development(
    context: Context, printer: Printer, enumerator: Printer.Enumerator, update: bool
) -> None:
    enumerator.do(f"{'Updating' if update else 'Pinning'} development dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                *_development_compile_args(update),
                "-o requirements-development.txt",
                "pyproject.toml",
            ],
        )


def _pin_or_update_production(
    context: Context, printer: Printer, enumerator: Printer.Enumerator, update: bool
) -> None:
    enumerator.do(f"{'Updating' if update else 'Pinning'} production dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                *_production_compile_args(update),
                "-o requirements.txt",
                "pyproject.toml",
            ],
        )


@task()
@task_banner("🔧🔧🔧", "Pinning\nDevelopment Dependencies")
def pin_development(context: Context) -> None:
    """Pins development dependencies from project file into requirements file for development."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=False)
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Pinning\nProduction Dependencies")
def pin_production(context: Context) -> None:
    """Pins production dependencies from project file into requirements file."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_production(context, printer, enumerator, update=False)
        enumerator.done()


@task(name="pin")
@task_banner("🔧🔧🔧", "Pinning\nDependencies")
def pin_dependencies(context: Context) -> None:
    """Pins dependencies from project file into requirements files."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=False)
        enumerator.done()
        _pin_or_update_production(context, printer, enumerator, update=False)
        enumerator.done()


@task(help={"apply": "Actually apply the updates instead of only previewing them."})
@task_banner("🔧🔧🔧", "Updating\nDevelopment Dependencies")
def update_development(context: Context, apply: bool = False) -> None:
    """Updates development dependencies from project file into requirements file for development.

    By default this only previews which dependencies would be updated and to
    which version. Pass --apply to actually perform the update.
    """
    printer = Printer()
    with printer.enumerator() as enumerator:
        if apply:
            _pin_or_update_development(context, printer, enumerator, update=True)
        else:
            enumerator.do("Previewing development dependency updates")
            _preview_update(
                context,
                printer,
                CONFIGURATION.project_paths.PROJECT / "requirements-development.txt",
                _development_compile_args(update=True),
            )
        enumerator.done()


@task(help={"apply": "Actually apply the updates instead of only previewing them."})
@task_banner("🔧🔧🔧", "Updating\nProduction Dependencies")
def update_production(context: Context, apply: bool = False) -> None:
    """Updates production dependencies from project file into requirements file.

    By default this only previews which dependencies would be updated and to
    which version. Pass --apply to actually perform the update.
    """
    printer = Printer()
    with printer.enumerator() as enumerator:
        if apply:
            _pin_or_update_production(context, printer, enumerator, update=True)
        else:
            enumerator.do("Previewing production dependency updates")
            _preview_update(
                context,
                printer,
                CONFIGURATION.project_paths.PROJECT / "requirements.txt",
                _production_compile_args(update=True),
            )
        enumerator.done()


@task(name="update", help={"apply": "Actually apply the updates instead of only previewing them."})
@task_banner("🔧🔧🔧", "Updating\nDependencies")
def update_dependencies(context: Context, apply: bool = False) -> None:
    """Updates dependencies from project file into requirements files.

    By default this only previews which dependencies would be updated and to
    which version. Pass --apply to actually perform the update.
    """
    printer = Printer()
    with printer.enumerator() as enumerator:
        if apply:
            _pin_or_update_development(context, printer, enumerator, update=True)
            enumerator.done()
            _pin_or_update_production(context, printer, enumerator, update=True)
            enumerator.done()
        else:
            enumerator.do("Previewing development dependency updates")
            _preview_update(
                context,
                printer,
                CONFIGURATION.project_paths.PROJECT / "requirements-development.txt",
                _development_compile_args(update=True),
            )
            enumerator.done()
            enumerator.do("Previewing production dependency updates")
            _preview_update(
                context,
                printer,
                CONFIGURATION.project_paths.PROJECT / "requirements.txt",
                _production_compile_args(update=True),
            )
            enumerator.done()


# endregion ⭐ Make Tasks ⭐
