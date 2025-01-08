from invoke.context import Context

from .core import run_in_context, task, task_banner
from .core.files import FilesCleaner
from .core.printer import Printer
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


def _pin_or_update_development(
    context: Context, printer: Printer, enumerator: Printer.Enumerator, update: bool
) -> None:
    enumerator.do(f"{'Updating' if update else 'Pinning'} development dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                *["--upgrade"] * update,
                "--extra build",
                "--extra test",
                "--extra check",
                "--extra tool",
                "--extra support",
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
                *["--upgrade"] * update,
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


@task()
@task_banner("🔧🔧🔧", "Updating\nDevelopment Dependencies")
def update_development(context: Context) -> None:
    """Updates development dependencies from project file into requirements file for development."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=True)
        enumerator.done()


@task()
@task_banner("🔧🔧🔧", "Updating\nProduction Dependencies")
def update_production(context: Context) -> None:
    """Updates production dependencies from project file into requirements file."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_production(context, printer, enumerator, update=True)
        enumerator.done()


@task(name="update")
@task_banner("🔧🔧🔧", "Updating\nDependencies")
def update_dependencies(context: Context) -> None:
    """Updates dependencies from project file into requirements files."""
    printer = Printer()
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=True)
        enumerator.done()
        _pin_or_update_production(context, printer, enumerator, update=True)
        enumerator.done()


# endregion ⭐ Make Tasks ⭐
